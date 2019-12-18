from flask import Flask, flash, current_app
from flask_sqlalchemy import SQLAlchemy
# from flask_sqlalchemy import BaseQuery, SQLAlchemy  # if we create custom query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy import or_
from datetime import datetime as dt
from dateutil import parser
import re
from statistics import mean, median, stdev
import json
from pprint import pprint  # only for debugging
# TODO: see "Setting up Constraints when using the Declarative ORM Extension" at https://docs.sqlalchemy.org/en/13/core/constraints.html#unique-constraint

db = SQLAlchemy()


def init_app(app):
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)  # Disabled since it unnecessary uses memory
    # app.config.setdefault('SQLALCHEMY_ECHO', True)  # Turns on A LOT of logging.
    # app.config['MYSQL_DATABASE_CHARSET'] = 'utf8mb4'  # Perhaps already set by default in MySQL
    db.init_app(app)


def metric_clean(metric_string):
    return re.sub('^carousel_album_', '', metric_string)


def from_sql(row, related=False, safe=False):
    """ Translates a SQLAlchemy model instance into a dictionary """
    data = row.__dict__.copy()
    data['id'] = row.id
    # current_app.logger.info('============= from_sql ===================')
    # current_app.logger.info(row.__class__)
    if related:
        rel = row.__mapper__.relationships
        # TODO: Attach rel to data
        pprint(rel)
    temp = data.pop('_sa_instance_state', None)
    if not temp:
        current_app.logger.info('Not a model instance!')
    if safe:
        Model = row.__class__
        data = {k: data[k] for k in data.keys() - Model.UNSAFE}
    return data


def fix_date(Model, data):
    datestring = ''
    if Model in {Insight, OnlineFollowers}:
        datestring = data.pop('end_time', None)
    elif Model == Audience:
        datestring = data.get('values', [{}])[0].get('end_time')  # We expect the list to have only 1 element.
    elif Model == Post:
        datestring = data.pop('timestamp', None)
    data['recorded'] = parser.isoparse(datestring).replace(tzinfo=None) if datestring else data.get('recorded')
    return data


# class GetActive(BaseQuery):
#     """ Some models, such as Post, may want to only fetch records not yet processed """
#     def get_active(self, not_field=None):
#         # if not not_field:
#         #     lookup_not_field = {'Post': 'processed', 'Campaign': 'completed'}
#         #     curr_class = self.__class__.__name__
#         #     not_field = lookup_not_field(curr_class) or None
#         return self.query.filter_by(processed=False)


class User(db.Model):
    """ Data model for user (influencer or brand) accounts.
        Assumes only 1 Instagram per user, and it must be a business account.
        They must have a Facebook Page connected to their business Instagram account.
    """
    roles = ('influencer', 'brand', 'manager', 'admin')
    __tablename__ = 'users'

    # TODO: https://techspot.zzzeek.org/2011/01/14/the-enum-recipe/
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.Enum(*roles, name='user_roles'), default='influencer', nullable=False)
    name = db.Column(db.String(47),                 index=False, unique=False, nullable=True)
    instagram_id = db.Column(BIGINT(unsigned=True), index=True,  unique=True,  nullable=True)
    facebook_id = db.Column(BIGINT(unsigned=True),  index=False, unique=False, nullable=True)
    token = db.Column(db.String(255),               index=False, unique=False, nullable=True)
    token_expires = db.Column(db.DateTime,          index=False, unique=False, nullable=True)
    notes = db.Column(db.String(191),               index=False, unique=False, nullable=True)
    modified = db.Column(db.DateTime,               index=False, unique=False, nullable=False, default=dt.utcnow, onupdate=dt.utcnow)
    created = db.Column(db.DateTime,                index=False, unique=False, nullable=False, default=dt.utcnow)
    insights = db.relationship('Insight',   backref='user', lazy=True, passive_deletes=True)
    audiences = db.relationship('Audience', backref='user', lazy=True, passive_deletes=True)
    posts = db.relationship('Post',         backref='user', lazy=True, passive_deletes=True)  # ? query_class=GetActive,
    # # campaigns = backref from Campaign.users with lazy='dynamic'
    # # brand_campaigns = backref from Campaign.brands with lazy='dynamic'
    UNSAFE = {'token', 'token_expires', 'modified', 'created'}

    def __init__(self, *args, **kwargs):
        kwargs['facebook_id'] = kwargs.pop('id') if 'facebook_id' not in kwargs and 'id' in kwargs else None
        kwargs['name'] = kwargs.pop('username', kwargs.get('name'))
        if 'token_expires' not in kwargs and 'token' in kwargs:
            # modifications for parsing data from api call
            token_expires = kwargs['token'].get('token_expires', None)
            kwargs['token_expires'] = dt.fromtimestamp(token_expires) if token_expires else None
            kwargs['token'] = kwargs['token'].get('access_token', None)
        super().__init__(*args, **kwargs)

    def insight_report(self, label_only=False):
        """ Used for reporting typical insight metrics for a Brand (or other user) """
        from .sheets import clean
        insight_metrics = list(Insight.metrics)
        measurements = [('Median', median), ('Average', mean), ('StDev', stdev)]
        insight_labels = [f"{metric} {ea[0]}" for metric in insight_metrics for ea in measurements]
        if label_only:
            return ['Brand Name', 'Notes', *insight_labels, 'instagram_id', 'modified', 'created']
        if self.instagram_id is None:
            insight_data = [0 for ea in insight_labels]
        else:
            temp = {key: [] for key in insight_metrics}
            for insight in self.insights:
                temp[insight.name].append(int(insight.value))
            insight_data = [ea[1](temp[metric]) for metric in insight_metrics for ea in measurements]
        report = [self.name, self.notes, *insight_data, getattr(self, 'instagram_id', ''), clean(self.modified), clean(self.created)]
        return report

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<User - {}: {}>'.format(self.role, self.name)


class OnlineFollowers(db.Model):
    """ Data model for 'online_followers' for a user (influencer or brand) """
    composite_unique = ('user_id', 'recorded', 'hour')
    __tablename__ = 'onlinefollowers'
    __table_args__ = (db.UniqueConstraint(*composite_unique, name='uq_onlinefollowers_recorded_hour'),)

    id = db.Column(db.Integer,      primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    recorded = db.Column(db.DateTime, index=False, unique=False, nullable=False)
    hour = db.Column(db.Integer,      index=False, unique=False, nullable=False)
    value = db.Column(db.Integer,     index=False, unique=False, nullable=True)

    def __init__(self, *args, **kwargs):
        kwargs = fix_date(OnlineFollowers, kwargs)
        super().__init__(*args, **kwargs)

    def __str__(self):
        return int(self.value)

    def __repr__(self):
        return f"<OnlineFollowers {self.recorded} | Hour: {self.hour} | User {self.user_id} >"


class Insight(db.Model):
    """ Data model for insights data on a (influencer or brand) user's account """
    composite_unique = ('user_id', 'recorded', 'name')
    __tablename__ = 'insights'
    __table_args__ = (db.UniqueConstraint(*composite_unique, name='uq_insights_recorded_name'),)

    id = db.Column(db.Integer,      primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    recorded = db.Column(db.DateTime,          index=False, unique=False, nullable=False)
    name = db.Column(db.String(47),            index=False, unique=False, nullable=False)
    value = db.Column(db.Integer,              index=False, unique=False, nullable=True)
    # # user = backref from User.insights with lazy='select' (synonym for True)
    influence_metrics = {'impressions', 'reach'}
    profile_metrics = {'phone_call_clicks', 'text_message_clicks', 'email_contacts',
                       'get_directions_clicks', 'website_clicks', 'profile_views', 'follower_count'}
    lifetime_metrics = {'online_followers'}
    metrics = influence_metrics.union(profile_metrics)
    UNSAFE = {''}

    def __init__(self, *args, **kwargs):
        kwargs = fix_date(Insight, kwargs)
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f"{self.user} Insight - {self.name} on {self.recorded}"

    def __repr__(self):
        return '<Insight: {} | User: {} | Date: {} >'.format(self.name, self.user, self.recorded)


class Audience(db.Model):
    """ Data model for current information about the user's audience. """
    # TODO: If this data not taken over by Neo4j, then refactor to parse out the age groups and gender groups
    composite_unique = ('user_id', 'recorded', 'name')
    __tablename__ = 'audiences'
    __table_args__ = (db.UniqueConstraint(*composite_unique, name='uq_audiences_recorded_name'),)

    id = db.Column(db.Integer,      primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    recorded = db.Column(db.DateTime,          index=False, unique=False, nullable=False)
    name = db.Column(db.String(47),            index=False, unique=False, nullable=False)
    value = db.Column(db.Text,                 index=False, unique=False, nullable=True)
    # # user = backref from User.audiences with lazy='select' (synonym for True)
    metrics = {'audience_city', 'audience_country', 'audience_gender_age'}
    UNSAFE = {''}

    def __init__(self, *args, **kwargs):
        kwargs = fix_date(Audience, kwargs)
        data, kwargs = kwargs.copy(), {}  # cleans out the not-needed data from API call
        kwargs['recorded'] = data.get('recorded')
        kwargs['user_id'] = data.get('user_id')
        kwargs['name'] = re.sub('^audience_', '', data.get('name'))
        kwargs['value'] = data.get('value', json.dumps(data.get('values', [{}])[0].get('value')))
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f"{self.user} Audience - {self.name} on {self.recorded}"

    def __repr__(self):
        return '<Audience {} | Date: {} >'.format(self.name, self.recorded)


class Post(db.Model):
    """ Instagram media that was posted by an influencer user """
    __tablename__ = 'posts'

    id = db.Column(db.Integer,          primary_key=True)
    user_id = db.Column(db.Integer,     db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id', ondelete='SET NULL'), nullable=True)
    processed = db.Column(db.Boolean, default=False)
    media_id = db.Column(BIGINT(unsigned=True), index=True,  unique=True,  nullable=False)
    media_type = db.Column(db.String(47),       index=False, unique=False, nullable=True)
    caption = db.Column(db.Text,                index=False, unique=False, nullable=True)
    comments_count = db.Column(db.Integer,      index=False, unique=False, nullable=True)
    like_count = db.Column(db.Integer,          index=False, unique=False, nullable=True)
    permalink = db.Column(db.String(191),       index=False, unique=False, nullable=True)
    recorded = db.Column(db.DateTime,           index=False, unique=False, nullable=False)  # timestamp*
    modified = db.Column(db.DateTime,           index=False, unique=False, nullable=False, default=dt.utcnow, onupdate=dt.utcnow)
    created = db.Column(db.DateTime,            index=False, unique=False, nullable=False, default=dt.utcnow)
    # The following 9 are from insights, the first 2 for all kinds of media
    impressions = db.Column(db.Integer,         index=False,  unique=False, nullable=True)
    reach = db.Column(db.Integer,               index=False,  unique=False, nullable=True)
    # The following 3 are for Album and Photo/Video media
    engagement = db.Column(db.Integer,          index=False,  unique=False, nullable=True)
    saved = db.Column(db.Integer,               index=False,  unique=False, nullable=True)
    video_views = db.Column(db.Integer,         index=False,  unique=False, nullable=True)
    # The following 4 are only for stories media
    exits = db.Column(db.Integer,               index=False,  unique=False, nullable=True)
    replies = db.Column(db.Integer,             index=False,  unique=False, nullable=True)
    taps_forward = db.Column(db.Integer,        index=False,  unique=False, nullable=True)
    taps_back = db.Column(db.Integer,           index=False,  unique=False, nullable=True)
    # # user = backref from User.posts with lazy='select' (synonym for True)
    # # campaign = backref from Campaign.posts with lazy='select' (synonym for True)

    metrics = {}
    metrics['basic'] = {'media_type', 'caption', 'comments_count', 'like_count', 'permalink', 'timestamp'}
    metrics['insight'] = {'impressions', 'reach'}
    metrics['IMAGE'] = {'engagement', 'saved'}.union(metrics['insight'])
    metrics['VIDEO'] = {'video_views'}.union(metrics['IMAGE'])
    metrics['CAROUSEL_ALBUM'] = {f"carousel_album_{metric}" for metric in metrics['IMAGE']}  # ?in metrics['VIDEO']
    metrics['STORY'] = {'exits', 'replies', 'taps_forward', 'taps_back'}.union(metrics['insight'])
    UNSAFE = {''}

    def __init__(self, *args, **kwargs):
        kwargs = fix_date(Post, kwargs)
        kwargs['processed'] = True if kwargs.get('processed') in {'on', True} else False
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f"{self.user} {self.media_type} Post on {self.recorded}"

    def __repr__(self):
        return '< {} Post | User: {} | Recorded: {} >'.format(self.media_type, self.user, self.recorded)


user_campaign = db.Table(
    'user_campaigns',
    db.Column('id',          db.Integer, primary_key=True),
    db.Column('user_id',     db.Integer, db.ForeignKey('users.id', ondelete="CASCADE")),
    db.Column('campaign_id', db.Integer, db.ForeignKey('campaigns.id', ondelete="CASCADE"))
)

brand_campaign = db.Table(
    'brand_campaigns',
    db.Column('id',          db.Integer, primary_key=True),
    db.Column('brand_id',    db.Integer, db.ForeignKey('users.id',    ondelete="CASCADE")),
    db.Column('campaign_id', db.Integer, db.ForeignKey('campaigns.id', ondelete="CASCADE"))
)


class Campaign(db.Model):
    """ Relationship between Users and Brands """
    __tablename__ = 'campaigns'

    id = db.Column(db.Integer,       primary_key=True)
    completed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(47),     index=True,  unique=True,  nullable=True)
    notes = db.Column(db.String(191),   index=False, unique=False, nullable=True)
    modified = db.Column(db.DateTime,   index=False, unique=False, nullable=False, default=dt.utcnow, onupdate=dt.utcnow)
    created = db.Column(db.DateTime,    index=False, unique=False, nullable=False, default=dt.utcnow)
    users = db.relationship('User', secondary=user_campaign, backref=db.backref('campaigns', lazy='dynamic'))
    brands = db.relationship('User', secondary=brand_campaign, backref=db.backref('brand_campaigns', lazy='dynamic'))
    posts = db.relationship('Post', backref='campaign', lazy=True)
    UNSAFE = {''}

    def __init__(self, *args, **kwargs):
        kwargs['completed'] = True if kwargs.get('completed') in {'on', True} else False
        super().__init__(*args, **kwargs)

    def report_columns(self):
        """ These are the columns used for showing the data for Posts assigned to a given Campaign """
        ignore = ['user_id', 'campaign_id', 'processed', 'media_id']
        columns = [ea.name for ea in Post.__table__.columns if ea.name not in ignore]
        return columns

    def get_results(self):
        """ We want the datasets and summary statistics """
        rejected = {'insight', 'basic'}
        added = {'comments_count', 'like_count'}
        lookup = {k: v.union(added) for k, v in Post.metrics.items() if k not in rejected}
        related, sets_list = {}, []
        for media_type, metric_set in lookup.items():
            temp = [metric_clean(ea) for ea in metric_set]
            sets_list.append(set(temp))
            related[media_type] = {'posts': [], 'metrics': {ea: [] for ea in temp}, 'labels': {ea: [] for ea in temp}}
        # add key for common metrics summary
        start = sets_list.pop()
        common = list(start.intersection(*sets_list))
        related['common'] = {'metrics': {metric: [] for metric in common}, 'labels': {metric: [] for metric in common}}
        # populate metric lists with data from this campaign's currently assigned posts.
        for post in self.posts:
            media_type = post.media_type
            related[media_type]['posts'].append(post)
            for metric in related[media_type]['metrics']:
                related[media_type]['metrics'][metric].append(int(getattr(post, metric)))
                related[media_type]['labels'][metric].append(int(getattr(post, 'id')))
                if metric in related['common']['metrics']:
                    related['common']['metrics'][metric].append(int(getattr(post, metric)))
                    related['common']['labels'][metric].append(int(getattr(post, 'id')))
        # compute stats we want for each media type and common metrics
        for group in related:
            related[group]['results'] = {}
            metrics = related[group]['metrics']
            for metric, data in metrics.items():
                curr = {}
                curr['total'] = sum(data) if len(data) > 0 else 0
                curr['mid'] = median(data) if len(data) > 0 else 0
                curr['avg'] = mean(data) if len(data) > 0 else 0
                curr['spread'] = stdev(data) if len(data) > 0 else 0
                related[group]['results'][metric] = curr
        return related
        # end get_results

    def __str__(self):
        name = self.name if self.name else self.id
        brands = ', '.join([brand.name for brand in self.brands]) if self.brands else 'NA'
        return f"Campaign: {name} with Brand(s): {brands}"

    def __repr__(self):
        name = self.name if self.name else self.id
        brands = ', '.join([brand.name for brand in self.brands]) if self.brands else 'NA'
        return '<Campaign: {} | Brands: {} >'.format(name, brands)


def db_create(data, Model=User):
    try:
        model = Model(**data)
        db.session.add(model)
        db.session.commit()
    except IntegrityError as error:
        # most likely only happening on Brand, User, or Campaign
        print('----------- IntegrityError Condition -------------------')
        pprint(error)
        db.session.rollback()
        columns = Model.__table__.columns
        unique = {c.name: data.get(c.name) for c in columns if c.unique}
        pprint(unique)
        model = Model.query.filter(*[getattr(Model, key) == val for key, val in unique.items()]).one_or_none()
        if model:
            message = f"A {model.__class__.__name__}, with already exists (id: {model.id}). Using existing."
        else:
            message = f'Cannot create due to collision on unique fields. Cannot retrieve existing record'
        current_app.logger.info(message)
        flash(message)
    # except Exception as e:
    #     print('**************** DB CREATE Error *******************')
    #     print(e)
    results = from_sql(model, safe=True)
    # safe_results = {k: results[k] for k in results.keys() - Model.UNSAFE}
    return results


def db_read(id, Model=User, safe=True):
    model = Model.query.get(id)
    if not model:
        return None
    output = from_sql(model, safe=safe)
    # safe_results = {k: results[k] for k in results.keys() - Model.UNSAFE}
    # output = safe_results if safe else results
    if Model == User:
        if len(model.insights) > 0:
            output['insight'] = True
        if len(model.audiences) > 0:
            output['audience'] = [from_sql(ea) for ea in model.audiences]
    return output


def db_update(data, id, Model=User):
    # Any checkbox field should have been prepared by process_form()
    model = Model.query.get(id)
    for k, v in data.items():
        setattr(model, k, v)
    db.session.commit()
    results = from_sql(model, safe=True)
    # safe_results = {k: results[k] for k in results.keys() - Model.UNSAFE}
    return results


def db_delete(id, Model=User):
    Model.query.filter_by(id=id).delete()
    db.session.commit()


def db_all(Model=User, role=None):
    """ Returns all of the records for the indicated Model, or for User Model returns either brands or influencers. """
    # current_app.logger.info('=============== called db_all =================')
    sort_field = Model.name if hasattr(Model, 'name') else Model.id
    query = (Model.query.order_by(sort_field))
    if Model == User:
        role_type = role if role else 'influencer'
        query = query.filter_by(role=role_type)
    models = query.all()
    return models


def create_many(dataset, Model=User):
    """ Currently only used for temporary developer_admin function """
    all_results = []
    for data in dataset:
        model = Model(**data)
        db.session.add(model)
        all_results.append(model)
    db.session.commit()
    return [from_sql(ea) for ea in all_results]


def db_create_or_update_many(dataset, user_id=None, Model=Post):
    """ Create or Update if the record exists for all of the dataset list """
    current_app.logger.info(f'============== Create or Update Many {Model.__name__} ====================')
    allowed_models = {Post, Insight, Audience}
    if Model not in allowed_models:
        return []
    # composite_unique = ['recorded', 'name'] if Model in {Insight, Audience} else False
    composite_unique = getattr(Model, 'composite_unique', None)
    # Note: initially all Models only had 1 non-pk unique field
    # However, those with table_args setting composite unique restrictions have a composite_unique class property.
    # insp = db.inspect(Model)
    all_results, add_count, update_count, error_set = [], 0, 0, []
    # print(f'---- Initial dataset has {len(dataset)} records ----')
    if composite_unique and user_id:
        q = Model.query.filter(Model.user_id == user_id)
        match = q.all()
        # print(f'------ Composite Unique for {Model.__name__}: {len(match)} possible matches ----------------')
        lookup = {tuple([getattr(ea, key) for key in composite_unique]): ea for ea in match}
        # pprint(lookup)
        for data in dataset:
            data = fix_date(Model, data)  # fix incoming data 'recorded' as needed for this Model
            # TODO: The following patch for Audience is not needed once we improve API validation process
            if Model == Audience:
                data['name'] = re.sub('^audience_', '', data.get('name'))
                data['value'] = json.dumps(data.get('values', [{}])[0].get('value'))
                data.pop('id', None)
            key = tuple([data.get(ea) for ea in composite_unique])
            model = lookup.get(key, None)
            # print(f'------- {key} -------')
            if model:
                # pprint(model)
                [setattr(model, k, v) for k, v in data.items()]
                update_count += 1
            else:
                # print('No match in existing data')
                model = Model(**data)
                db.session.add(model)
                add_count += 1
            all_results.append(model)
    else:
        # The following should work with multiple single column unique fields, but no composite unique requirements
        # print('----------------- Unique Columns -----------------------')  # TODO: remove
        columns = Model.__table__.columns
        unique = {c.name: [] for c in columns if c.unique}
        [unique[key].append(val) for ea in dataset for (key, val) in ea.items() if key in unique]
        # pprint(unique)
        # unique now has a key for each unique field, and a list of all the values that we want to assign those fields from the dataset
        q_to_update = Model.query.filter(or_(*[getattr(Model, key).in_(arr) for key, arr in unique.items()]))
        match = q_to_update.all()
        # match is a list of current DB records that have a unique field with a value matching the incoming dataset
        # print(f'---- There seems to be {len(match)} records to update ----')
        match_dict = {}
        for key in unique.keys():
            lookup_record_by_val = {getattr(ea, key): ea for ea in match}
            match_dict[key] = lookup_record_by_val
        for data in dataset:
            # find all records in match that would collide with the values of this data
            updates = [lookup[int(data[unikey])] for unikey, lookup in match_dict.items() if int(data[unikey]) in lookup]
            if len(updates) > 0:
                if len(updates) == 1:
                    model = updates[0]
                    for k, v in data.items():
                        setattr(model, k, v)
                    update_count += 1
                    all_results.append(model)
                else:
                    # print('------- Got a Multiple Match Record ------')
                    data['id'] = [getattr(ea, 'id') for ea in updates]
                    error_set.append(data)
            else:
                model = Model(**data)
                db.session.add(model)
                add_count += 1
                all_results.append(model)
    current_app.logger.info('------------------------------------------------------------------------------')
    current_app.logger.info(f'The all results has {len(all_results)} records to commit')
    current_app.logger.info(f'This includes {update_count} updated records')
    current_app.logger.info(f'This includes {add_count} added records')
    current_app.logger.info(f'We were unable to handle {len(error_set)} of the incoming dataset items')
    current_app.logger.info('------------------------------------------------------------------------------')
    db.session.commit()
    return [from_sql(ea) for ea in all_results]


def _create_database():
    """ May currently only work if we do not need to drop the tables before creating them """
    app = Flask(__name__)
    app.config.from_pyfile('../config.py')
    init_app(app)
    with app.app_context():
        # db.drop_all()
        # print("All tables dropped!")
        db.create_all()
    print("All tables created")


if __name__ == '__main__':
    _create_database()

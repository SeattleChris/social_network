# Feature Development Plan for March 2020 - ver 0.3.0

## Milestones

| Complete           | Task                                         |
| ------------------ |:--------------------------------------------:|
|                    | **Initial Features Completion**              |
| :heavy_check_mark: | Initial Features from [checklist](./checklist.md) |
|                    | **Milestone 1 Completion**                    |
| :heavy_check_mark: | Initial Investigation of media files complexity |
| :heavy_check_mark: | Update Feature Goals & Documentation         |
| :heavy_check_mark: | Separate Dev site owned by Bacchus           |
| :heavy_check_mark: | Campaign - Sort Posts by published date      |
| :heavy_check_mark: | Favicon and robots.txt files                 |
| :heavy_check_mark: | Integrate Flask-Migrate to assist ongoing DB changes |
|                    | **Milestone 2 Completion**                   |
| :heavy_check_mark: | Update Posts model (db structure) to Many-to-Many w/ campaigns |
| :heavy_check_mark: | Posts can be assigned to multiple campaigns  |
| :heavy_check_mark: | Rejecting & accepting Posts only affects current Campaign |
| :heavy_check_mark: | View & re-evaluate rejected Campaign Posts [stretch goal] |
| :heavy_check_mark: | Remove dev only logging, code clean-up       |
| :heavy_check_mark: | Migrate live DB (and deploy all of above)    |
|                    | **Milestone 3 Completion**                   |
| :heavy_check_mark: | Saving Story Post media files                |
| :heavy_check_mark: | Can view saved media in Campaign processing  |
|                    | **Milestone 4 Completion**                   |
| :heavy_check_mark: | Story Webhook for full data at expiration    |
| :heavy_check_mark: | Sheet Report layout update, multi-worksheets |
| :heavy_check_mark: | Update documentation to capture all updates  |
|                    | **Completed Stretch Goals**                  |
| :heavy_check_mark: | Security: encrypting stored tokens           |
| :heavy_check_mark: | Campaign sheet reports include saved media   |
| :heavy_check_mark: | Separate Capture application & resources.    |
| :heavy_check_mark: | Capture app self-updates OS and Browser      |
| :heavy_check_mark: | Task Queue managing calling Capture app      |
|                    | Secure Queue on gRPC protocol, save response |
| :heavy_check_mark: | On User delete, remove metrics & keep Posts  |
| :heavy_check_mark: | Admin feature: check permissions a User granted |
| :white_check_mark: | Update documentation to capture all updates  |
|                    | **Suggested Stretch Goals**                  |
|                    | On User delete, delete Posts not in Campaign |
|                    | Saving Post images if in a Campaign          |
|                    | Capture app API turned off when not needed   |
|                    | New manager/admin account password set on first login |
|                    | Sheet permission given to user creating it   |
|                    | Handle a User delete request from Facebook   |
|                    | Post model can track is_story separate from media_type |
|                    | Refactor for Post.is_story & Post.media_type |
|                    | Creating batches for daily API call          |
|                    | Default user who always gets Sheet access    |
|                    | Sheet management: Delete, Modify access, etc |
|                    | Tests: ensure future dev doesn't break existing functions |
|                    | **March 2020 Features Completed**            |
| :heavy_check_mark: | Migrate live DB (and deploy all of above)    |
| :heavy_check_mark: | Run functions needed for migrate steps       |
| :heavy_check_mark: | Confirm Onboarding, including page subscribe |

## Checklist

### Key

- [x] Completed.
- [n] No: does not work or decided against.
- [ ] Still needs to be done.
- [c] Needs to be confirmed.
- [?] Unsure if needed.
- [s] Stretch Goal. Not for current feature plan.

Current Status:
2020-05-04 20:40:42
<!-- Ctrl-Shift-I to generate timestamp -->

### Story Metrics Update

- [x] WebHook to get Stories data at completion
  - [x] Must have FB permissions `instagram_manage_insights`
  - [x] App must be installed on the FB page associated with the IG business account.
    - [x] Can determine the page for users we already have.
    - [x] Update User model, onboarding(), and decide_ig form to track the page_id.
    - [x] User model has field to track if installing the app was successful.
    - [x] Onboarding process records the page_id to the created User account.
    - [x] App is automatically installed when page_id & page_token is added or updated on User account.
      - [x] triggered by a signal and listener on the page_id field for all users.
      - [x] Record success state of installing app for User
  - [x] Have a hook route on live site
  - [x] Configure hook route on FB App Dashboard
  - [x] Security: confirm signature with SHA1 generated with payload and App Secret
    - [x] FB_HOOK_SECRET for Graph to send in query to our hook route.
  - [ ] Once confirmed, remove story data update from daily cron job
- [x] ? What storage structure is needed for larger media files ?
  - [x] Probably need to setup a storage bucket
  - [n] ? Maybe saved to our App instance ?

### Capture Media Image Files for Stories

- [x] Do not require extra work from Influencers
- [n] Ver A: Investigate if any possible API technique
- [n] Ver B: Web Scrapper the obscured media files
- [n] Ver C: Web Scrapper and screen capture, see Capture Media Files
- [x] Ver D: Create a separate media capture service and API
  - [n] Google Cloud Functions can run code, but not resources for browser.
  - [n] GCP App Engine - Standard can not install browser and run on its resources.
  - [x] GCP App Engine - Flex environment can install via Docker, custom runtime.
    - [x] Create Dockerfile that builds on python3.7, installs Chrome and & Chromedriver
      - [x] Dockerfile is self-maintaining for Chrome, installs up-to-date stable version.
      - [x] Dockerfile can determine correct chromedriver, install and configure as needed.
      - [x] Dockerfile is self-maintaining for linux, python3.7, chrome, chromedriver.
    - [x] Captured media storage
      - [x] Proof-of-life: save to the filesystem of the instance.
      - [x] Connect to a Storage bucket.
      - [x] Save files to Storage bucket instead of filesystem.
  - [n] Setup GCP Compute Engine w/ Chrome and Flask app to capture.
    - [?] Compute Engine Flask App can continue running: see `screen` .
    - [?] Make startup script for Compute Engine to launch Flask App and keep it running.
    - [?] Compute Engine Flask App can save to a bucket.
    - [s] Compute Engine Code and Resources can be easily maintained and updated.
      - [s] Create Docker Container of the code.
      - [s] Technique to install and/or update Chrome.
      - [s] Technique to determine the correct chromedriver version, then install and/or update it.
      - [s] Refactor the startup script for starting the Flask App.
      - [s] Technique to stage update dependencies in our Docker to be tested.
      - [s] Tests of functionality for our API and Docker to confirm updates can go live.
- [x] Associate captured Story media content if it is later assigned to a campaign.
- [x] API associates captured media files to a Post, creating a directory matching Post id.
- [x] Update Post model to have a `saved_media` field for a url string of the media files location.
  - [x] update code.
  - [x] migrate Dev DB.
- [x] API returns a `url_list` whose value represents where the captured media files can be accessed.
- [c] Campaign sheet report includes a column for this captured and saved media content.
- [s] Non-Story Post media files.
  - [x] Current: permalink given. Require manager to screen capture and crop.
  - [s] Capture media file only if associated to a campaign.
    - [s] Use the same technique used for Story media files.
- [s] Process for releasing and deleting saved media files.
  - [s] At what point is a Story old enough, and still not in a Campaign, it should be deleted?
  - [s] Should we delete or put into some other long-term storage for old Campaign media files?
- [x] Document in API that 'saved_media' and 'post_model' are reserved keys in response.
- [?] Capture before story is assigned to campaign, before it expires
  - [x] Temp solution: attempt capture when created or updated.
  - [ ] Task Queue to manage calling the Capture API.
    - [x] Able to create a task queue to capture stories.
    - [?] Able to create a task queue to capture other posts.
    - [x] Able to use existing task queue (story or post captures).
    - [ ] ? Need to call update_queue when adding a task to keep extending the queue expiration.
    - [x] Determine and set appropriate retry settings, especially for Story captures.
    - [x] Able to add a task to a capture queue.
    - [x] Update Post model to store the task name once it is assigned.
    - [x] Post model has field(s) for tracking and reporting captured media image links.
    - [ ] Update Post instances with links to the captured media images.
      - [ ] Another queue to read completed capture queue tasks?
      - [ ] ? Refactor capture queue to route on current app service (default for prod, dev for dev)?

### Capture Media Image Files Process for Posts including stories

- [n] If we know the file, or can traverse web page to it.
  - [x] from bs4 import BeautifulSoup, also use requests, urllib.request, time.
  - [x] I do not think this will work since IG is a React App.
- [x] Install selenium, and maybe we can traverse result page with BeautifulSoup.
  - [x] Can we get a Chrome instance to give the needed data for BeautifulSoup?
  - [x] Can we traverse the DOM to get the img files?
- [x] Install selenium and with a chrome instance, do a screenshot.
- [x] Running Locally:
  - [x] Can visit the desired location.
  - [x] Save the full page screenshot.
  - [x] Can save file in a sub-directory.
    - [x] It is relative to the root of the repo, not relative to the application folder.
  - [n] Can install Chrome browser used just by project, and connect to it and not existing Chrome.
- [x] Running from Server:
  - [x] Can install Chrome browser so it can be run as a headless browser.
  - [x] Setup browser emulation when called on server.
  - [x] Can visit the desired location.
  - [x] Save the full page screenshot.
  - [x] Save a screenshot for each candidate image file, if possible.
- [x] Store the file in a desired location.
  - [x] assigned file directory.
  - [n] Media / Static files location.
  - [x] storage bucket location.
- [x] Make the stored file available as a link.
- [x] Link to file is stored as property on the Post object.
  - [n] ? Replace permalink with our created link to the media file?
  - [x] Add another field in the DB for our local_permalink
- [x] Function called for Story Media right after story media is discovered.
- [s] Determine options for video files.
  - [s] Can we grab the entire video?
  - [s] Can we grab a frame of the video, or default view?
- [s] After story media files works, apply to other media files content.
  - [s] Make it a function called when create a sheet report.
- [c] Sheet Report can have a link to the file as stored by us.
- [s] The actual file is copied to the worksheet in the Sheet Report.

Also see items in the [test-site-content checklist](https://github.com/SeattleChris/test-site-content/blob/master/checklist.md)

### Campaign & Posts Management

- [x] Campaign Manage View - Assigning Posts
  - [x] Posts ordered by published date
    - [x] Is this true for Sheet Report?
  - [x] Fix Campaign template error on |length
  - [x] Fix references to no longer used fields:
    - [x] Post.processed
    - [x] Post.campaign_id
    - [x] Post.campaign
    - [x] Campaign.posts
  - [x] Using new fields and methods:
    - [x] Refactored Campaign relationships. Now Campaign.processed and Campaign.posts
      - [x] Previously was Campaign.rejected, Campaign.posts
      - [x] Campaign.processed has both rejected and accepted posts
    - [x] Post related models refactored.
      - [x] Old fields and methods Post.rejections, Post.campaigns
      - [x] backref from Campaigns gives Post.campaigns and Post.processed
    - [x] User methods for campaign posts refactored as Campaign.related_posts(value)
      - [x] valid value are Campaign views: 'management', 'collected', 'rejected'
      - [x] Old User methods: campaign_posts(), campaign_rejected(), campaign_unprocessed()
  - [n] Assign & Remove from all Queue
  - [x] Assign & Keep in all Queue
  - [x] Reject & remove from only this Campaign Queue
  - [x] Un-assign & Add back to this Campaign Queue
  - [x] Un-assign & Remove from this Campaign Queue
  - [n] Un-assign & Add back to all Queue
  - [n] Un-assign & Remove from all Queue
  - [s] Un-assign & assign to different related campaign
  - [x] Update & Improve wording for processing Campaign Posts
  - [x] View and modify Posts that had been rejected for this campaign
  - [?] In all Campaign views, report what other Campaigns a Post belongs to if any
  - [s] Cleaner written template radio input logic: if a view then value=0 checked, else other value

### DB Design & Setup

- [x] Integrate flask-migrate
  - [x] Install package, update requirement files
  - [x] Initial migration creation
  - [x] test changes and migration management
- [x] Post model to Campaign is Many-to-Many relationship
  - [x] Additional fields or methods tracking what queues it is removed from
- [x] Post.rejections to Post.processed, Campaign.rejected to Campaign.processed
- [s] Update ON DELETE for a User's posts.
- [s] How do we want to organize audience data?
- [s] Refactor Audience Model to parse out the gender and age group fields
  - [s] After refactor, make sure audience data does not overwrite previous data
- [x] Set order_by='recorded' inside db.relationship declarations?
  - [x] Confirm this does not break templates somehow?
- [x] fix data.brands (Campaign.brands): TypeError: object of type 'AppenderBaseQuery' has no len()
- [x] Encrypt tokens
- [n] Keep a DB table of worksheet ids?
  - [s] Will we have multiple report views?
- [x] DB Migration: Integrate flask-migrate?
- [s] ?Delete User information in response to a Facebook callback to delete.?
- [x] Allow a user to delete their account on the platform
  - [x] Confirmation page before delete?
  - [ ] What about posts assigned to a campaign?
    - [x] Keep all old posts
    - [x] Campaign collected can still see posts from deleted users if already in campaign
    - [x] Campaign results still works with posts from deleted users
    - [?] Campaign sheet report still works with posts from deleted users
    - [s] Keep posts only currently in a campaign, discard unattached posts
  - [ ] What about unassigned posts for this User?
    - [s] Each post should be deleted
    - [?] Any reference to this post (Campaign.processed) should be handled ON DELETE
- [c] Revisit structure for ON DELETE, ON UPDATE (especially on User delete)
- [c] Revisit structure for how related tables are loaded (lazy=?)
- [s] Revisit method of reporting Campaign Results

### Google Drive & Sheets Functionality

- [x] Improve Google Sheet Report
  - [x] Export Sheet functions should use multiple worksheets/tabs in the same file.
  - [?] Check if Google Sheets has a max of 26 columns and 4011 rows.
  - [x] Media content is accessible from the Google Sheet
    - [c] ? Link to the content ?
    - [s] ? Embed the content ?
  - [s] Regex for A1 notation starting cell.
- [s] When Export Sheet is created (for Campaign or User), current_user gets sheet permissions
- [s] When Export Sheet is created, access is granted to some universal Admin
- [s] Embed the worksheet as a view in our app (after admin login feature)
- [s] For a given worksheet, ability to delete existing permissions
- [s] For a given worksheet, ability to delete the file
- [s] Attach worksheets to the Campaign model so we not always creating new.

### Login & Authentication Features

- [?] Fix brand select an IG account
- [s] Update User name method
  - [x] Old: temporary name if we do not have one while we are waiting for their IG account selection
  - [s] ? Use their email address from facebook ?
  - [s] ? Other plan ?
- [c] Fix: The 'add admin' from admin list does not work because it should redirect.
- [s] Allow admin to create a user w/o a password.
  - [s] Require the user to set password on first login.
- [?] ?Confirm Google login for Worksheet access?
- [s] Auth management features:
  - [s] Change password
  - [s] Recover account (via email)

### Permissions to Routes and Showing/Hiding links in Templates

- [x] Any Routes / Template views needed to also have limited access?
  - [x] Remove Influencer and Brand user link to export to sheet. Admin only feature.
- [s] Other Security checks?
- [x] Delete Campaign link limited to just Admin.
  - [s] What if a manager accidentally created one?
- [s] Global revoke permissions to all Sheet/file in Drive for a given user.

### Site Content & Style

- [s] Update Style for major launch
  - [s] Page styling of admin sections to assist in clear reports and navigation
  - [s] Attractive page styling for Influencer sign up portal & documents (ToS, privacy, etc)
  - [s] Content for Influencer sign-up portal (home view) to give them confidence in the process.
  - [s] Attractive and clear styling for profile and data views seen by Influencers.
- [x] favicon (looks nice in browser, less search engine errors)
- [x] Confirm all templates build off a template that points to favicon location
  - [x] extends "base.html" is safe
  - [x] extends "view.html" is safe
  - [x] extends "campaign.html" is safe
  - [x] All template files are extensions of base or other confirmed sources.
- [?] Error response using template vs app.errorhandler(500).
- [?] Turn off the extra info for an error 500 for deployed live site.
- [x] Add robots.txt file so search engines are not getting errors.

### Other Site Functionality

- [s] Limit request fetch more Posts to only get new posts since last request
- [s] Fetching Posts - Visual feedback that it is processing but not ready to render new view
- [x] Catch and handle if trying to create an already existing Campaign name
  - [x] Note: Does not update with new inputs I believe
  - [s] Stop and redirect to create new campaign
    - [s] With link to existing campaign of matching name
- [x] Re-Login method for existing account for an Influencer or Brand user
  - [x] Note: Currently a bit of a kludge solution for them to login to existing account
  - [s] TODO: Actual login process does not create and then delete a new account for existing user login
- [s] ?Properly implement Facebook callback to delete some user data ?
- [s] User detail view reports current number of posts we have stored
- [s] Post Detail view
  - [s] Sort or Filter to show posts by processed or not yet processed
  - [s] Sort or Filter to show posts that are assigned to a campaign
  - [s] Sort or Filter to show posts that were rejected from being in a campaign
- [s] Research Google Cloud settings to remove delay for website to spin up after idle.

### Code Structure, Testing, Clean up

- [x] Setup Dev Version as owned by Bacchus
  - [x] Env has DEV site & config settings depend on DEV_RUN flag
  - [x] Project created under Bacchus billing account - devfacebookinsights
  - [x] App Engine created in that Project - Chris does not have permission
  - [x] Connect Dev DB (cloned in Facebook Insights App)
    - [x] Ver A) Set permissions and confirm it can connect across Projects
    - [n] Ver B) Re-assign the cloned/dev DB to the Dev Project
    - [n] Ver C) See if the DB image/clone can be used to create DB in Dev Project.
- [x] Remove very excessive logs. Keeping high log level until onboarding is verified.
  - [x] Modify to use logger.debug as appropriate
  - [x] Modify to use logger.exception as appropriate
  - [x] Change settings so live site does not log DEBUG
  - [x] ? Change settings so live site does not log INFO ?
- [c] Remove excessive logs after we confirm numerous onboarding.
- [?] Check and comply to expected response on a cron job.
- [x] Flatten Migrate files to not create and delete unneeded changes (esp. test changes)
- [x] Migrate Live DB (test with having Dev site connect to it before deploy live code?)
- [x] Set DEV_RUN=False, and deploy to live site.
- [s] Update forms and API digesting with input validation to replace following functionality:
  - [x] Currently fix_date used for both create model, and when create_or_update many
  - [x] Currently create_or_update_many also has to modify inputs from Audience API calls
  - [x] Should campaign management view extend base instead of view?
- [c] Is current onboard process slow? Delay some data collection?
- [c] Other feedback for expected sign up flow?
- [s] Form Validate: Add method to validate form. Safe against form injection?
- [s] Error handling on adding user with duplicate email address.
- [s] Error handling on adding user with duplicate name.

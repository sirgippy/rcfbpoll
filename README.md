# The /r/CFB Poll

A weekly college football top 25 poll managed and voted on by users of [/r/CFB](https://reddit.com/r/CFB/), the college football subreddit.

## About

This is the code repository for the /r/CFB Poll, hosted at https://poll.redditcfb.com/ where a select group of users of the subreddit [/r/CFB](https://reddit.com/r/CFB/) vote weekly on their top 25 football teams. The poll is currently managed by myself ([u/sirgippy](https://reddit.com/user/sirgippy)) and the other /r/CFB moderators. The poll has been in operation since 2010 and this is the third iteration of the poll site, currently built in django and Python 2.7 while making heavy use of Boostrap and jQueryUI.

I like the added features of taiga.io versus the issue board on GitHub, so you can find the backlog [here](https://tree.taiga.io/project/gippy-rcfb-poll-website-rebuild/backlog) and an issue board [here](https://tree.taiga.io/project/gippy-rcfb-poll-website-rebuild/issues?page=1&orderBy=status).

The site was developed using Ubuntu, but has been confirmed to work on OS X and should be fine on any other \*nix. It's probably possible to get it working in Windows too, but would probably require some finagling. It's deployed to Heroku.

The site exclusively uses [Python Social Auth](https://github.com/python-social-auth/social-core) and OAuth2 interactions on reddit to handle authentication. This is great from a poll management perspective, but can make administrative set-up and local deployment a bit more difficult.

## Installation & Setup

### -1. Get Python 2.7 if you don't already have it and set up your virtual environment

I recommend using a virtual environment because some of the dependencies are old and probably shouldn't be your default versions.

Hoping to update to Python 3 soon but for now 🤷

### 0. Clone the repository

### 1. Install the required dependencies

The site is currently configured to use PostgreSQL. If you don't already have it, install it first ([OS X setup tutorial](https://www.codementor.io/engineerapart/getting-started-with-postgresql-on-mac-osx-are8jcopb)).

Then, install the other python package dependencies, e.g. 

    pip install -r requirements.txt
    pip install -r requirements_local.txt

(If you're on OS X and get a bug installing six, see [here](https://stackoverflow.com/a/37026323).)

### 2. Download and run the database

Using django to provision a new database and have the site work is currently not possible as the site uses virtual models and queries are needed within the database to get the results views to work. Future versions may alleviate this requirement or provide scripts to get up and going, but at present we'll need a copy of the existing database.

A dump of the live site's database as of 10/8/2018 is [here](https://drive.google.com/open?id=1B0Am9pi0M-X5dKCQ41M3v5zURpb0-N0w).

If you're using PostgreSQL, use `psql rcfbpoll -f rcfbpoll.dump` to install it. Either match the credentials listed in `/rcfbpoll/settings/base.py` or adjust `base.py` to match the db's credentials as you set them. __Don't create a django superuser yet;__ This will be done in a future step.

### 3. Register your local deployment on reddit

After logging into reddit, go to preferences > apps, scroll to the bottom, and click "create app". Fill out the form as required; the only field that actually matters is the "redirect uri" field. In that put `https://127.0.0.1:8000/complete/reddit/` (or whatever you plan to use as your local domain).

Once your local deployment has been registered, you'll need to set up the key and secret provided to be imported in the django settings.

As configured, the site currently expects environment variables `REDDIT_KEY` and `REDDIT_SECRET` for each of the two strings provided. Alternatively, you could copy-paste them directly into `/rcfbpoll/settings/base.py`.

### 4. Test and set up a superuser

You should now be ready to run the site and successfully log in. To run the site, use

    python manage.py runsslserver 127.0.0.1:8000
    
Use your favorite browser to navigate to the site (ignore the certificate warning) and attempt to log in.

If successful, congratulations! You have successfully set up a local deployment of the poll site. As a last step, you should use the django shell to give yourself superuser privileges as ascribed [here](https://stackoverflow.com/questions/11337420/can-i-use-an-existing-user-as-django-admin-when-enabling-admin-for-the-first-tim). You'll then be able to access the django admin console and create new objects on the site.

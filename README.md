# Backend

## Setup

Welcome! Before you get coding, there's a few setup-related tasks to complete. Specifically, you'll have to **1) fork the repo**, **2) configure your workflow**, and **3) setup your development environment**. After that, you should be able to get up and running.

### 1) Git going

First, you'll need to fork the Backend repo and sync it upstream.

*To fork the repo*, simply click the "Fork" button near the top right of this page. If prompted to select "where" to fork it, click your username.

*To clone your forked repo* to your local file system, first, navigate to the forked repo in your browser (**not** the original repository). Click the large green "Clone" button, and copy the URL onto your clipboard. Then, in a terminal window, navigate to where you want the project to live on your local file system (my recommendation is in a directory named "tagg" where you can store both your frontend & backend projects), and run the following command, replacing the dummy URL with your clipboard contents:

`git clone https://github.com/your-username/Backend.git`

You'll be prompted for your GitHub username & password, which you should enter. If, when working with GitHub in the future, you don't want to enter your credentials each time, check out [this guide](https://help.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh).

Now you have a local copy of your forked project on your computer, but it's not yet synced with the original repository. To sync your fork upstream, navigate to your repository in a terminal window. Inside the project directory, run the command

`git remote add upstream https://github.com/TaggiD-Inc/Backend.git`

Double check that this succeeded by running

`git remote -v`

in your project directory. If this worked, in addition to the two "origin" remotes, you should see two more "upstream" remotes.

If you've made it here with no errors, congratulations! You now have a local copy of the project. If you had any problems, feel free to consult your teammates.

### 2) Workflow

Next, you'll learn how to pull updates from the main repository, install dependencies, and configure your local git settings.

In order to pull updates from the main repository into to your local project, navigate to your local project and run the command

`git pull upstream master`

Your local project will then have the up-to-date project code from the main repository, but your fork on GitHub ("origin") will be now outdated. To push these local updates to your forked repository's master branch, run the command

`git push origin master`

In order to run your Django server, your project dependencies, those in `requirements.txt`, need to be installed. These dependencies are not uploaded to GitHub, so you'll need to navigate into your project directory and run (ensuring that your virtual environment is active, see #3 for instructions on how to set that up)

`pip install -r requirements.txt`

which will install the needed python packages. Make sure to perform this step each time you pull from upstream, as dependencies may be added and removed throughout the course of the project.

To work on a new feature, checkout a new branch in your local project with the command

`git checkout -b tmaXX-name-of-feature`

where "tmaXX-name-of-feature" refers to the Jira ticket number and feature name (e.g. tma1-setup-mysql-ec2).

To push your changes on your feature branch to your fork, run the command

`git push origin tmaXX-name-of-feature`

The first time you push a local feature branch to your fork, run the above command with the `-u` flag (e.g. `git push -u origin tmaXX-name-of-feature`). This sets up the upstream branch. Detailed instructions can be found [here](https://devconnected.com/how-to-push-git-branch-to-remote/).

To ensure your master branch is up-to-date with the main repository, run this command from your master branch

`git pull upstream master`

To view your branches and see which one you're currently on, run

`git branch` (exit that view with `q`)

To switch branches, run

`git checkout branch-name` (e.g. `git checkout master`)

Once you finish building and testing a feature with the most up-to-date project code from the main repository, commit and push your local updates to your GitHub fork, then merge the *feature branch* of your forked repository (i.e origin) into the *master branch* of the main repository (i.e upstream) through a GitHub pull request. This can be done in a browser by navigating to your forked repository and the branch to merge on GitHub.

Lastly, your commits need to be signed. [Click here](https://help.github.com/en/github/authenticating-to-github/signing-commits) to learn how to set that up. We'll be using GPG keys for signing commits. The GitHub help site doesn't mention it, but there are a few extra items to configure after creating and uploading your key. Specifically, run the commands

- `git config --global commit.gpgsign true`
- `git config --global gpg.program gpg`
- `git config --global user.signingkey XXXXXXXXXXXXXXXX` (replacing `XXXXXXXXXXXXXXXX` with your 16-digit GPG key)
- `echo 'export GPG_TTY=$(tty)' >> ~/.bash_profile && source ~/.bash_profile` (replacing `~/.bash_profile` with your shell's configuration file. If you are on macOS and using zsh, this is `~/.zshrc`; check your shell with `echo $SHELL`)

Lastly, ensure that you see your full name and GitHub email when running

- `git config --global user.name`
- `git config --global user.email`

If not, set them by simply running the same command but with your name and email as an argument (enclosed in quotes, e.g. `git config --global user.name "FIRST LAST"`).

In the future, all commits made from the command line should be done with the `-S` flag (e.g. `git commit -S -m "commit message"`). This tells git to sign the commit.

If you've made it here, congratulations! You are one step closer to being fully set up. Again, if this is not the case, feel free to consult your teammates.

### 3) Setting up your development environment

Ensure that you have `python3` installed. Then, from your repo's root directory, run `python3 -m venv env` to create your virtual environment. Once it is created, you can activate it by running `source env/bin/activate`. In order to deactivate your virtual environment, you can run `deactivate`. Make sure that the environment is activated at all times when you are working on the project, as it sets the correct python version, and has the required packages. 

Environment variables are managed in `manager/manager/vars.env`. They are imported automatically into `manager/settings.py`. If your feature requires definining new environment variables, or updating existing ones, you can do so in `vars.env`.

## Migrating

Every time Django models are updated, or new migrations are created, you will have to migrate the database. You can do this by running the two following commands:

`python manage.py makemigrations` and `python manage.py migrate`

## Running

To run your Django server, open a terminal window, navigate to your project directory, activate your virtual environment, and run `python manage.py runserver`. This should run your Django server on localhost. Any time you edit your code while the server is running, Django will refresh the server to reflect your code edits in real time (live reload on save). Happy coding!

## Notes

If you use Apple's newest m1 chips, you might need to add the following to get commands to work:
`arch -x86_64`
to designate architecture.

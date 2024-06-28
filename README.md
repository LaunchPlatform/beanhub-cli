# beanhub-cli [![CircleCI](https://dl.circleci.com/status-badge/img/gh/LaunchPlatform/beanhub-cli/tree/master.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/gh/LaunchPlatform/beanhub-cli/tree/master)
Command line tools for BeanHub or Beancount users.

## Features

- **Local BeanHub Form web app** - You can run a [BeanHub Form](https://beanhub.io/blog/2023/07/31/automating-beancount-data-input-with-beanhub-custom-forms/) web app locally to try out your forms
- **Import** - Simple yet powerful [beanhub-import](https://github.com/LaunchPlatform/beanhub-import) allows you to define importing rules in YAML to extract transactions from CSV files and generate Beancount transactions automatically
- **Formatter** - Advanced Beancount file formatter based on top of [beancount-black](https://github.com/LaunchPlatform/beancount-black)
- **Basic Beancount file manipulations** - Effortless Beancount account name renaming and other basic manipulations (coming soon)
- **Doesn't require a BeanHub account** - While some features in the future will require a BeanHub repository to operate, but we make most of them usable even without a BeanHub account

## Screenshots

<p align="center">
  <img src="https://github.com/LaunchPlatform/beanhub-cli/raw/master/assets/forms-screenshot.png?raw=true" alt="BeanHub Forms Screenshot" />
</p>

# Sponsor

<p align="center">
  <a href="https://beanhub.io"><img src="https://github.com/LaunchPlatform/beanhub-cli/raw/master/assets/beanhub.svg?raw=true" alt="BeanHub logo" /></a>
</p>

A modern accounting book service based on the most popular open source version control system [Git](https://git-scm.com/) and text-based double entry accounting book software [Beancount](https://beancount.github.io/docs/index.html).

## Install

```bash
pip install beanhub-cli
```
## Usage

## BeanHub Import

To run BeanHub's import feature locally, you can define your import rules at `.beanhub/imports.yaml` and then run the following command in your Beancount folder:

```bash
bh import
```

To learn more about the import document and how the BeanHub import feature works, you can read the README of [beanhub-import](https://github.com/LaunchPlatform/beanhub-import).

### BeanHub Forms web app

To make it much easier for BeanHub users to test their BeanHub Forms locally, we added a simple local web app for that in beanhub-cli.
You can run it by

```bash
bh form server
```

It should open the BeanHub Forms web page locally at http://localhost:8080 by default.
It reads the `.beanhub/forms.yaml` file from the current directory and will modify beancount files in the directory, so make sure you cd to your beancount directory before running the command.
To learn more about BeanHub Forms, please read our blog post [Automating Beancount data input with custom forms makes your life 10 times easier!](https://beanhub.io/blog/2023/07/31/automating-beancount-data-input-with-beanhub-custom-forms/).

### List BeanHub Forms

To list BeanHub Forms, simply run

```bash
bh form list
```
### Validate BeanHub Forms doc

To validate BeanHub Forms doc, simply run

```bash
bh form validate
```

### Format beancount files

You can run [beancount-black](https://github.com/LaunchPlatform/beancount-black) formatter against given files by the following command

```bash
bh format main.bean
```

Without the file arguments, the format command will try to format `main.bean` in the current folder, and it will recursively follow all the `include` statements to format all the bean files.
Like this:

```bash
bh format
```

### More features to come

We are working on basic beancount file manipulation features, such as renaming account names.
We will also add new features only for BeanHub users as well.
But in general, if possible, we would like to make the features added to beancount-cli work locally without a BeanHub account as much as possible so that the beancount community can benefit from it.

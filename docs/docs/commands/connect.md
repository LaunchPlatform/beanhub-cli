# BeanHub Connect

!!! note
    This command requires you to run the login command first.
    Please read the [document about the login command first here](./login.md).

[BeanHub Connect](https://beanhub.io/blog/2024/06/24/introduction-of-beanhub-connect/) is a feature for paid BeanHub members only.
This feature allows our members to [connect to 12,000+ financial institutions in 17 countries and produce CSV files](https://beanhub.io/blog/2024/06/24/introduction-of-beanhub-connect/), which [beanhub-import](https://github.com/LaunchPlatform/beanhub-import) can ingest and generate corresponding Beancount transactions for you automatically.
Originally, this feature imports data as Git commits only to BeanHub's repository.
Later on, we added the standalone commands to make it possible to pull bank transactions directly into your local work environment without relying on updates in BeanHub's Git repository.
You can read our blog post [Direct Connect: Pulling transactions as CSV files from banks via Plaid directly](https://beanhub.io/blog/2025/01/16/direct-connect-repository/) to learn more.

## Pre-requirements

To pull transaction data from your bank automatically, you need to first log into your BeanHub account on our web app and then go to your repository.
Find the `Import` item in the left side menu and click `Connected Banks`.

![Screenshot of BeanHub Connect list](/img/beanhub-connect-list.png){: .center }

Next, it will prompt you with the Plaid dialogue to choose and authenticate the bank you want to connect to.

![Screenshot of Plaid prompt dialogue in BeanHub Connect list page](/img/beanhub-connect-pop-up.png){: .center }

After finishing the connect step, the BeanHub system will have a default schedule to pull new data from your bank via Plaid.
BeanHub encrypts and secures all your transaction data with [HSM (Hardware Security Module)](https://en.wikipedia.org/wiki/Hardware_security_module) in our database.
You can customize the update schedule as you please on the same `Connected Banks` page in your repository.

## Sync

While most BeanHub users rely on BeanHub to pull transaction data from banks via Plaid and then run BeanHub Import automatically in our cloud infrastructure, some users may want to run BeanHub Import workflow locally.
To ensure that all the transaction data in BeanHub's database is up-to-date, you can run a sync command to make BeanHub update transactions from the banks for you immediately instead of waiting until the scheduled time arrives.

To run the sync command, simply type:

```bash
bh connect sync
```

## Dump

Our open-source Beancount transactions import library, [beanhub-import](https://github.com/LaunchPlatform/beanhub-import), relies on the users to provide CSV files from banks.
Usually, this part is done on BeanHub's server along with sync operations and provides the changes as a new Git commit.
Some users prefer to have their workflow stay local, or they prefer to manually check before making a commit.
In that case, the dump command comes in handy.
The dump command collects all the transactions we synced from Plaid previously with either the sync command or scheduled sync operations and dumps them into your local file system as CSV files.
To run the command, simply type:

```bash
bh connect dump
```

Since many users may want to run a sync before the dump, we also provide a `--sync` argument to make it run sync first, then dump to ensure that your transaction data is up-to-date.
Like this:

```bash
bh connect dump --sync
```

## Dump detailed accounts information

In some cases, you may want to get detailed information about the bank accounts, such as the current balance, currency, full name, and type of account.
You can enrich the transactions with detailed bank account information during your automatic import process.
To do so, you only need to run the dump command with the `--output-accounts` argument pointing to the filename or folder to dump the account CSV file.
For example:

```bash
bn connect dump --output-accounts=my-accounts.csv
```

If the provided output accounts path is a directory, the default output filename would be `accounts.csv`.
Like this:

```bash
bn connect dump --output-accounts=my-folder
```

It will end up outputting the accounts CSV file at `my-folder/accounts.csv.`

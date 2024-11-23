# Format beancount files

You can run [beancount-black](https://github.com/LaunchPlatform/beancount-black) formatter against given files by the following command

```bash
bh format main.bean
```

Without the file arguments, the format command will try to format `main.bean` in the current folder, and it will recursively follow all the `include` statements to format all the bean files.
Like this:

```bash
bh format
```

## Rename account and currency (commodity)

The main purpose of the format command is to format Beancount files.
It reads and parses the Beancount file as a syntax tree, then transforms it and eventually outputs it back as a Beancount file.
This process also provides a great opportunity to perform extra transformation to the tree, such as renaming an account or currency.
Therefore, we implement account and currency renaming in this command.

To rename an account, you can pass in `--rename-account <from> <to>` to the format command. You can also use `-ra` for short.
For example, to rename `Liabilities:CreditCard:AmericanExpress` to `Liabilities:CreditCard:Amex`, you can simply run this:

```bash
bh format -ra Liabilities:CreditCard:AmericanExpress Liabilities:CreditCard:Amex
```

You can rename multiple accounts at once by passing `-ra` multiple times.
Like this:

```bash
bh format \
  -ra Liabilities:CreditCard:AmericanExpress Liabilities:CreditCard:Amex \
  -ra Expenses:Food Expenses:Food:Dining
  
```

You can also rename currency by passing `--rename-currency <from> <to>`.
Like the option for renaming an account, you can also pass in `-rc` for short.
Here's an example of renaming currency from `BTC` to `BITCOIN` by running.

```bash
bh format -rc BTC BITCOIN
```

You can also combine multiple account and currency renaming options in the same format run.

```bash
bh format \
  -ra Liabilities:CreditCard:AmericanExpress Liabilities:CreditCard:Amex \
  -ra Expenses:Food Expenses:Food:Dining \
  -rc BTC BITCOIN
  
```

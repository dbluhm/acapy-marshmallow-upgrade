# ACA-Py Marshmallow Upgrade Tool

This is a very quick and dirty migration tool for ACA-Py's use of Marshmallow.
This will find and modify as many instances of a Marshmallow field definition as
possible, run them through an AST transformer, and print them back out to the
file.

## Dependencies

This tool assumes `ripgrep` is available on your system. Usage of `ripgrep`
could probably be trivially changed to just a recursive grep if necessary.

This tool also assumes `gawk` is available on your system.

## Usage

Copy the files of this project into your local fork of ACA-Py.

```sh
$ cp ./* ../aries-cloudagent-python/.
$ cd ../aries-cloudagent-python
```

(Create and) enter virtual environment:

```sh
$ python -m venv env  # If needed
$ source env/bin/activate
```

Install dependencies:

```sh
$ pip install -r requirements.txt
$ pip install astor
```

Execute the script:

```sh
$ ./upgrade-marshmallow.sh
```

## How it works

First, this tool will guess which files require modification by performing a
search for python files containing `marshmallow`. This is expected to match
files needing modification since most will import `marshmallow`.

Then, for each matched file, this tool will run `marshmallow.awk` and capture
the output in a temporary file. `marshmallow.awk` executes `marshmallow.py` as a
co-process and will feed discovered field definitions into this python script
over its `stdin` and read the modified field definition from its `stdout`.

`marshmallow.py` uses an AST parser, transformer, and printer to read in python
statements, modify them as needed, then print them back out as valid python.
There are, technically, two transformers. One that moves keyword unexpected
arguments to the metadata keyword and one that updates keyword arguments that
have been deprecated (`missing` becomes `load_default`, for example).
Indentation of each python statement is manually saved and restored.

The temporary file is then moved to replace the original file.

After all files containing `marshmallow` are processed with `marshmallow.awk`,
the script will run `black` on the `aries_cloudagent` package to correct the
formatting of the modified fields back to what is expected in ACA-Py.

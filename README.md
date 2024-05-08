# Automata-Based Presburger Arithmetic SMT Solver

This is a SMT solver for Presburger arithmetic (or linear integer arithmetic) based on automata.

This project is in progress.

## Installation
Install [rye](https://rye-up.com/guide/installation/), `gcc`, and `clang`
### for Mac
Install graphviz via homebrew.
```bash
brew install graphviz
```
You need to add these path to install `pygraphviz` in rye.
```bash
export CFLAGS="-I $(brew --prefix graphviz)/include"
export LDFLAGS="-L $(brew --prefix graphviz)/lib"
```
Then run `rye sync` to install all the dependencies.

### for Linux
Install graphviz via apt.
```bash
sudo apt-get install graphviz graphviz-dev
```
Then run `rye sync` to install all the dependencies.

## Usage

TODO

# 卒論

オートマトンを用いたプレスブルガー算術式の充足可能性判定法

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [参考文献](#参考文献)
- [License](#license)

## Installation(for Mac and Linux)
Install [rye](https://rye-up.com/guide/installation/), `gcc`, and `clang` if you haven't.

Install graphviz via homebrew.
```bash
brew install graphviz
```
You need to add these path to install `pygraphviz` to rye.
```bash
export CFLAGS="-I $(brew --prefix graphviz)/include"
export LDFLAGS="-L $(brew --prefix graphviz)/lib"
```
Then run `rye sync`.

## Usage

TODO

## 参考文献

## License

TODO

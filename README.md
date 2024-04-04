<h1 align=center>
  <img width=64 src=https://github.com/greeeen-dev/unifier/assets/41323182/3065245a-28b6-4410-9b07-8b940f4796ae>
  
  Unifier Micro (microfier)</h1>
<p align=center>A much lighter version of <a href="https://github.com/greeeen-dev/unifier">Unifier</a></p>

## What is Unifier Micro?
Unifier Micro is a much lighter and less performant version of Unifier, built to work on extremely low-end systems. 
Memory usage is minimized by removing certain values from `UnifierMessage` class, as well as not utilizing caching 
and multithreading.

## Who should use this?
Unifier Micro is built for small communities just wanting to give Unifier a spin, or communities with very limited 
resources to run Unifier. For communities of scale with decent resources, we recommend using the [full-scale 
version](https://github.com/greeeen-dev/unifier) instead.

## Features
### Simple and efficient bridge
Unifier Micro's bridge has been rewritten to be as simple and resource efficient as possible. Although this results 
in significant performance losses, it is still usable enough for small communities.

### Moderation commands
Unifier Micro comes with basic server-side and global moderation commands for safety, such as user and server banning. 
Bot admins can assign moderators to Unifier Micro, just like in Unifier.

### Still database-free
Just like in Unifier, there's no need to spend time setting up databases for Unifier Micro. Everything is stored 
locally on the same system you use to run Unifier Micro, so the performance is not impacted by slow 10k+ ping database 
servers.

## Setup
Unifier setup guides can be used to set up Unifier Micro, although some parts won't apply to Unifier Micro (such as 
installing Upgrader).

- [If you're using an existing Unifier client](https://unichat-wiki.pixels.onl/setup/getting-started)

- [If you're hosting your own Unifier client](https://unichat-wiki.pixels.onl/setup-selfhosted/getting-started)

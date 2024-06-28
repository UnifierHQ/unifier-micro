<h1 align=center>
  <img width=64 src=https://github.com/UnifierHQ/unifier-micro/assets/41323182/16f7ca32-bc5a-47d2-89ae-50ebef8ef70d>
  
  Unifier Micro</h1>

<p align=center>A much lighter version of <a href="https://github.com/UnifierHQ/unifier">Unifier</a></p>

> [!NOTE]
> Unifier Micro is **not** the same as Unifier. If you're looking for the full scale version, go
> [here](https://github.com/UnifierHQ/unifier) instead.

## What is Unifier Micro?
Unifier Micro is a much lighter and less performant version of Unifier, built to work on extremely low-end systems. 
Memory usage is minimized by removing certain values from `UnifierMessage` class, as well as not utilizing 
multithreading and reducing caching.

## How is this different from Unifier?
Unifier is a much faster and versatile global chat bot. It uses threading and caching to significantly increase the 
bridging speed, and supports other platforms. Unifier Micro, on the other hand, takes a low-memory approach, and lacks 
the performance optimizations and platform support to significantly reduce memory usage. This reduces Unifier Micro's 
speed, as well as limits the bot to support Discord only.

## Who should use this?
Unifier Micro is built for small communities just wanting to give Unifier a spin, or communities with very limited 
resources to run Unifier. For communities of scale with decent resources, we recommend using the [full-scale 
version](https://github.com/UnifierHQ/unifier) instead.

## Features
### Basic features
Like most bridge bots, Unifier Micro has basic commands such as link, unlink, etc., so you can do most of what you'd 
need to do.

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

- [If you're using an existing Unifier client](https://unifier-wiki.pixels.onl/setup/getting-started)

- [If you're hosting your own Unifier client](https://unifier-wiki.pixels.onl/setup-selfhosted/getting-started)

## License
Unifier Micro is licensed under the AGPLv3. If you wish to use its source code, please read the license carefully before 
doing so.

## Support
If you need support with Unifier Micro, join our [Discord server](https://discord.gg/a4KpNcARzK). Or, you can open a question in 
issues.

If you're using a modified version, please ask that version's maintainer for support. We do not provide official support for 
modified versions of Unifier Micro.

## Acknowledgments
We want to thank:
- [**Voxel Fox**](https://github.com/Voxel-Fox-Ltd), for continuing the discord.py project as Novus when it was discontinued (it
  is now re-continued, but for now we'd like to use Novus)
- [**Rapptz**](https://github.com/Rapptz) and [**discord.py**](https://github.com/Rapptz/discord.py) developers, for creating the
  discord.py library Novus is based on

We also use the logging logger formatting code from discord.py, which is licensed under the MIT license. You can find more info in 
the `EXTERNAL_LICENSES.txt` file.

## Special thanks
As the project founder and leader, I want to give my special thanks to:
- [**ItsAsheer/NullyIsHere**](https://github.com/NullyIsHere), for joining the team and helping me fix my shitty Python and
  adding a lot of amazing features to Unifier
- [**Ente Community**](https://github.com/ente-io), for offering me invaluable advice for open sourcing this project
- **My best friend**, for turning my life around for the better and always supporting me even at my worst

And lastly but *most importantly*, **the late role model of mine I used to know very well**: He's the one that brought me and my 
best friend together, as well as lots of other people together as well. Without him, I don't know if Unifier would have even existed, 
so I want to pick up where he left off and continue uniting people in his honor. I dedicate this project to him by open sourcing the 
code, so people can use it to bring people together just like how he did.

In return, we expect that all users honor those who made this project possible use the code **responsibly**. Please do not organize 
any hate groups or whatever with Unifier.

## Note
Unifier's icon was co-created by @green. and @thegodlypenguin on Discord.

Unifier Micro and UnifierHQ developers are not affiliated or associated with, or endorsed by Discord Inc.

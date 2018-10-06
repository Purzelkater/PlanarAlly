.. _server:

Server Management
==================

A collection of information for when you host a PlanarAlly server.

Updating
-----------

Updating the server is typically a straightforward process. First you need to make a backup of your save files and assets.
Then you'll need to download the newest version. and lastly you'll potentially need to run a conversion script.

ALWAYS FIRST MAKE A BACKUP !!

Backup
-------

In particular the planar save files, all files that start with 'planar.save' in the root PlanarAlly folder are very important and should be backed up before upgrading.
Additionally it is advised to also backup the assets folder (PlanarAlly/static/assets) as this contains all the images that are uploaded to this server and are used in the various games.

If you use a compiled binary, you absolutely must make a copy of the above mentioned files/folders as the download of the newest release will almost definitely overwrite your saves and assets with default data!

Install new version
--------------------

After backing up everything safely, you'll have to download the newest version and install it as usual.

When using the compiled binary, download the zip file, extracting the data to the same folder as your last installation.

If you use git, a simple pull is all you'll typically need and in this case your save and asset data will typically not be touched, you're still strongly advised to make a backup though.

Conversion
-----------

Some updates will have changes to the save format and thus require some changes to your local saves before you can run your server.
As a safety precaution a server will not start if it detects that the save file is not updated.

To convert your save file, you'll need to run a conversion script, this is typically provided with the update.

The conversion files are located in the scripts folder and should be run from within the folder with the save file. (e.g. `python ../scripts/convert/3_to_4.py`)

For the compiled binaries, a conversion procedure is in the works.
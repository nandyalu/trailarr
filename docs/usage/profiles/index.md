Profiles allow you to define how and when trailers should be downloaded and processed in Trailarr.

Profiles are made up of two things:

- Settings: Audio, Video, and File settings
- Filters: Conditions that determine when the profile should be applied to a media item.

!!! tip ""
    This might probably be too much information, you can skip to the [Usage](#usage) section to understand how profiles are used in Trailarr or directly to the [Examples](examples.md) page.

You can create different profiles for different types of media or situations. 

For example, you can create a profile for `movies` with high-quality trailers, another for `series` with specific audio settings, or a profile that only applies to `media` in a certain `language`.

Profiles are located in the `Settings > Profiles` page of the Trailarr app [http://localhost:7889/settings/profiles](http://localhost:8000/settings/profiles){:target="_blank"}.

!!! tip
    The next sections will explain what each of the settings and filters do, how to create a profile, and how to use profiles in Trailarr.



### View Profiles

A list of existing profiles can be viewed in the `Profiles` page.

Click on any of the profiles to view its details.


### Create Profile

Clicking on the `Add New` button on the `Profiles` page will allow you to create a new profile.

- A dialog will open where you can set the profile name, filters, and settings for the profile. _Don't worry, you can change these settings later._
- Once you are done, click on the `Create` button to create the profile.
- This will take you to the profile settings page where you can edit the settings for the profile.

!!! info "Not saved until you click Create"
    The profile is not saved until you click the `Create` button. 
    
    - If you are trying to figure out what Filters to use, just add a Filter like `ID > 999999` and then click `Create`. 
    - This will create a profile with just one filter which you know will never match any media, which you can then edit later.

### Edit Profiles

To edit an existing profile, click on the relevant profile in the `Profiles` page.

!!! info "Edit Profile Name"
    To edit a profile name, click on the `✏️` (pencil) icon next to the profile name on the profile details page.

!!! tip "Edit the JSON directly"
    You can also edit the profile JSON directly by clicking on the `Edit JSON` button at the very end of the profile details page. This is useful for advanced users who want to edit the profile settings directly.

!!! tip "Duplicate Profile"
    You can duplicate a profile by clicking on the `Duplicate` button at the top right corner of the profile details page. This will open the [Create Profile](#create-profile) dialog, edit the name and click `Create` to create a new profile with the same settings as the original profile, which you can then edit as needed.

### Delete Profiles

To delete a profile, open the Profile edit page and click on the `Delete` button at the top right corner.


## Usage

Trailarr uses profiles as follows:

- When downloading a trailer from the UI. A dialog will appear allowing you to select a profile from existing profiles. Filters will not be applied in this case.
- When running the `Download Missing Trailers` task (which runs periodically). 
    - If no profiles are available, the task will not run.
    - Profiles with high priority will be used first.
    - The task will use the first profile that matches all the filters for each media item.
    - Media items that does not match any profiles will not be processed.
    - Media items that matches a profile but does not have a valid Media folder or `monitor` set to `false` will not be processed.

The next sections will explain the settings and filters available in profiles. You can instead skip to the [Examples](examples.md) page to see some examples of profiles and how they can be used.


!!! help "Trailarr is evolving"
    Trailarr is still evolving and the profiles feature is still being developed. If you have any suggestions or feedback, please join our [Discord server](https://discord.gg/KKPr5kQEzQ){:target="_blank"} and join the discussion.

    Things that are planned for the future:

    - Improve Profiles to make downloading Season specific trailers easier.
    - Maybe (maybe, no promises!) let the user download Featurettes, Clips, etc. as well.
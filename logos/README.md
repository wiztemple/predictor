# Team logos

Drop downloaded logos into `logos/inbox/`, in any file name and any format (PNG, SVG, WebP, JPG).
Sub-folders per league or country are welcome (e.g. `inbox/england/`), but not required.

Claude then matches each file to the team's name in our data (hand-checked, like
team_names.yaml), converts it to a small web-ready image and copies it to
`web/public/teams/`. Teams without a logo keep the coloured initials badge.

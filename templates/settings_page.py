"""Starter Settings page — copy this into your app's pages/ folder (e.g.
as pages/settings.py) and adjust the `from app_config import config` line
below if your app's config module is named differently.

Shows the logged-in user and a self-service change-password form to
everyone. Admins (see `ngfw.auth.is_admin`) additionally see a "Backup"
card (only if `AppConfig.backup_source_dir` is set — see `ngfw.backup`)
with a "Backup now" button, and a "Users" section for listing/adding
accounts and promoting/demoting admins. A non-admin visiting this page
just sees their own password form.

This page itself stays open to any logged-in user (`requires_auth=True`,
the default) so self-service password changes keep working for everyone.
If you'd rather lock the whole page to admins, add `requires_admin=True`
to the `@ngfw.page(...)` call below instead — but then no one else can
change their own password from the UI.
"""
from nicegui import ui

import ngfw
from ngfw import components

from app_config import config  # adjust to match your app's config module


@ngfw.page("/settings", "Settings", icon="settings", group="Account")
def settings_page() -> None:
    with ngfw.frame(config, "/settings"):
        ui.label("Settings").classes("text-2xl font-bold")
        me = ngfw.auth.current_user()
        am_admin = ngfw.auth.is_admin()
        suffix = " (admin)" if am_admin else ""
        ui.label(f"Logged in as {me}{suffix}").classes("text-grey-8 mb-2")

        # -- change your own password -----------------------------------
        with components.form_card("Change password"):
            new_password = components.labeled_input(
                "New password",
                password=True,
                password_toggle_button=True,
                validation={"Required": components.required(), "At least 8 characters": components.min_length(8)},
            )
            confirm_password = components.labeled_input(
                "Confirm new password", password=True, password_toggle_button=True
            )

            def change_password() -> None:
                if not new_password.validate():
                    return
                if new_password.value != confirm_password.value:
                    ui.notify("Passwords don't match", color="negative")
                    return
                ngfw.auth.create_user(me, new_password.value)  # overwrites your own password hash, keeps your role
                new_password.value = ""
                confirm_password.value = ""
                ui.notify("Password updated", color="positive")

            ui.button("Update password", on_click=change_password).props("color=primary")

        if not am_admin:
            return

        # -- admins only: on-demand backup, if periodic backups are set up
        if config.backup_source_dir:
            with components.form_card("Backup"):
                ui.label(
                    "A zip backup of the data folder runs automatically in the "
                    "background (see AppConfig.backup_interval_seconds). "
                    "Trigger one right now if you want a fresh copy immediately:"
                ).classes("text-xs text-grey-7 mb-2")

                def backup_now() -> None:
                    try:
                        path = ngfw.backup.make_backup(config)
                    except ValueError as exc:
                        ui.notify(str(exc), color="negative")
                    else:
                        ui.notify(f"Backup created: {path.name}", color="positive")

                ui.button("Backup now", icon="backup", on_click=backup_now).props("color=primary outline")

        # -- admins only: users list + add-user + promote/demote ---------
        with components.form_card("Users"):
            user_list = ui.column().classes("gap-1 w-full mb-2")

            def refresh_users() -> None:
                user_list.clear()
                with user_list:
                    for username in ngfw.auth.list_users():
                        with ui.row().classes("items-center gap-2 w-full"):
                            label = username + ("  (you)" if username == me else "")
                            ui.label(label).classes("text-sm").style("flex-grow: 1")
                            ui.switch(
                                "admin",
                                value=ngfw.auth.is_admin(username),
                                on_change=lambda e, u=username: toggle_admin(u, e.value),
                            )

            def toggle_admin(username: str, new_value: bool) -> None:
                try:
                    ngfw.auth.set_admin(username, new_value)
                except ValueError as exc:
                    ui.notify(str(exc), color="negative")
                else:
                    ui.notify(f"{'Promoted' if new_value else 'Demoted'} '{username}'", color="positive")
                finally:
                    refresh_users()  # redraw switches to match actual stored state either way

            refresh_users()

            ui.separator().classes("my-2")
            ui.label("Add a user").classes("text-sm font-medium")
            new_username = components.labeled_input("Username", validation={"Required": components.required()})
            new_user_password = components.labeled_input(
                "Password",
                password=True,
                password_toggle_button=True,
                validation={"Required": components.required(), "At least 8 characters": components.min_length(8)},
            )
            new_user_admin = ui.checkbox("Admin")

            def add_user() -> None:
                if not new_username.validate() or not new_user_password.validate():
                    return
                username = new_username.value.strip()
                if ngfw.auth.user_exists(username):
                    ui.notify("That username already exists", color="negative")
                    return
                ngfw.auth.create_user(username, new_user_password.value, is_admin=new_user_admin.value)
                new_username.value = ""
                new_user_password.value = ""
                new_user_admin.value = False
                refresh_users()
                ui.notify(f"Added user '{username}'", color="positive")

            ui.button("Add user", on_click=add_user).props("color=primary outline")

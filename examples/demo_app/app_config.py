"""The app's single AppConfig instance, split into its own module so both
main.py and every page module can import it without a circular import
(main.py imports the pages package, and pages need the config)."""
import ngfw

config = ngfw.AppConfig(
    title="Ngfw Demo",
    subtitle="reference app",
    favicon="🧭",
    primary_color="#1976d2",
    storage_secret="demo-only-change-me",
    users_file="demo_users.json",
)

from .settings import AppSettings, AppRuntime

app_settings = AppSettings()
app_settings.load()

app_runtime = AppRuntime()
app_runtime.load()

from .settings import AppSettings, AppRuntime, SyncedFiles

app_settings = AppSettings()
app_settings.load()

app_runtime = AppRuntime()
app_runtime.load()

synced_list = SyncedFiles()
synced_list.load()

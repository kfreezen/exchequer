from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="allow", env_file=".env")

    show_only_approved: bool = True
    apple_team_id: str = ""
    apple_services_id: str = "io.exchequer.app"
    apple_sso_key_id: str = ""
    apple_sso_key_path: str = ""

    google_client_id: str = ""
    google_client_ids_file: str = "/config/google_client_ids.txt"

    base_api_url: str = "https://api.exchequer.io"
    base_app_url: str = "https://exchequer.io"

    database_dsn: str = (
        "postgresql://exchequer:themasterkey@exchequer-postgres:5432/exchequer"
    )
    jwt_signing_key: str = "/config/jwt-key.pem"
    jwt_public_key: str = "/config/jwt-key.pem.pub"
    bucket_storage: str = "/data/"

    email_tagline: str = "Exchequer"
    smtp_hostname: str = "mail.exchequer.io"
    smtp_username: str = ""
    smtp_email: str = "support@exchequer.io"
    smtp_password: str = "password"
    friendly_from: str = "Exchequer Support"
    ses_region: str = "us-west-2"
    ses_api_key: str = ""
    ses_api_secret: str = ""

    debug: bool = False

    environment: str = "staging"
    sentry_dsn: str = ""
    sentry_traces_sample_rate: float = 0.0
    sentry_profiles_sample_rate: float = 0.0

    redis_url: str = "redis://redis:6379/0"
    anthropic_api_key: str = ""

    stripe_public_key: str = "You find this in the Stripe dashboard"
    stripe_secret_key: str = "You find this in the Stripe dashboard"

    log_level: str = "INFO"

    cookie_domain: str = ".exchequer.io"

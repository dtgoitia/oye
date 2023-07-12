use std::env;

use crate::oye::OyeApiBaseUrl;
use reqwest::Url;

#[derive(Debug)]
pub struct Config {
    pub oye_api_url: OyeApiBaseUrl,
}

#[derive(Debug)]
pub struct ConfigError {
    pub reason: String,
}

fn get_url_from_env_var(key: &str) -> Result<Url, ConfigError> {
    let raw = match env::var(&key) {
        Ok(value) => value,
        Err(_) => {
            return Err(ConfigError {
                reason: format!("environment variable '{}' not found", &key),
            })
        }
    };

    match Url::parse(&raw) {
        Ok(url) => Ok(url),
        Err(_) => {
            return Err(ConfigError {
                reason: format!("environment variable '{}' is not valid URL: {}", &key, &raw),
            })
        }
    }
}

pub fn get_config() -> Result<Config, ConfigError> {
    Ok(Config {
        oye_api_url: get_url_from_env_var("OYE_API_URL")?,
    })
}

use std::env;
use std::fs;

use crate::oye::OyeApiBaseUrl;
use reqwest::Url;
use serde::Deserialize;

#[derive(Debug)]
pub struct Config {
    pub oye_api_url: OyeApiBaseUrl,
}

#[derive(Debug, Deserialize)]
pub struct ConfigFile {
    pub api_url: Option<String>,
}

type EnvironmentVariableName = String;
type Reason = String;

#[derive(Debug)]
pub struct Error {
    pub reason: Reason,
}

#[derive(Debug)]
pub enum ConfigError {
    MissingEnvironmentVariable(EnvironmentVariableName),
    UnsupportedEnvironmentVariableValue(Reason),
}

fn load_config_from_user_config_file() -> Result<ConfigFile, String> {
    // try to load from config file in ~/.config/oye.yml
    let home_str = std::env::var("HOME")
        .expect("could not find HOME environment variable, are you in Linux/Mac?");
    let home = std::path::Path::new(&home_str);
    let path = home.join(".config/oye/config.yaml");

    if path.exists() == false {
        return Err(format!("config file not found: {}", path.to_str().unwrap()));
    }

    let mut config_file = ConfigFile { api_url: None };

    let content = fs::read_to_string(&path).unwrap();

    let parsed_yaml = serde_yaml::from_str::<ConfigFile>(&content);
    if let Ok(raw) = parsed_yaml {
        config_file.api_url = raw.api_url;

        // Add the rest of the config fields here
    } else {
        println!(
            "WARNING: failed to parse {}, reason: {}",
            path.to_str().unwrap(),
            parsed_yaml.err().unwrap().to_string()
        );
    }

    Ok(config_file)
}

fn get_url_from_env_var(key: &str) -> Result<Url, ConfigError> {
    let raw = match env::var(&key) {
        Ok(value) => value,
        Err(_) => return Err(ConfigError::MissingEnvironmentVariable(key.to_string())),
    };

    match Url::parse(&raw) {
        Ok(url) => Ok(url),
        Err(_) => {
            let reason = format!("environment variable {} is not valid URL: {:?}", &key, &raw);
            return Err(ConfigError::UnsupportedEnvironmentVariableValue(reason));
        }
    }
}

pub fn get_config() -> Result<Config, Error> {
    // try to load from config file in ~/.config/oye.yml
    let config_file = match load_config_from_user_config_file() {
        Ok(config) => Some(config),
        Err(reason) => {
            println!("WARNING: {}", reason);
            None
        }
    };

    // then, check if env_vars are set, and overrides values
    // if a field is not present in config file nor envvar, then fail
    let oye_api_url = match get_url_from_env_var("OYE_API_URL") {
        Ok(url) => url,
        Err(ConfigError::MissingEnvironmentVariable(env_var_name)) => {
            let api_url_not_set = format!(
                "oye API URL is not set, please add it to ~/.config/oye.yaml or as {}",
                env_var_name
            );

            if config_file.is_none() {
                return Err(Error {
                    reason: api_url_not_set,
                });
            }

            match config_file.unwrap().api_url {
                Some(url_str) => Url::parse(&url_str).unwrap(),
                None => {
                    return Err(Error {
                        reason: api_url_not_set,
                    });
                }
            }
        }
        Err(ConfigError::UnsupportedEnvironmentVariableValue(reason)) => {
            return Err(Error { reason })
        }
    };

    Ok(Config { oye_api_url })
}

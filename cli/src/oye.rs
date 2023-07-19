use crate::config::Config;
use reqwest;
use serde::{Deserialize, Serialize};

pub type OyeApiBaseUrl = reqwest::Url;

#[derive(Debug)]
pub struct OyeClient {
    pub base_url: OyeApiBaseUrl,
    client: reqwest::blocking::Client,
}

#[derive(Debug)]
pub enum OyeClientError {
    FailedToGetReminders(String),
    FailedToCreateReminder(String),
    FailedToDeleteReminder(String),
}

impl OyeClient {
    pub fn new(config: &Config) -> OyeClient {
        OyeClient {
            base_url: config.oye_api_url.clone(),
            client: reqwest::blocking::Client::new(),
        }
    }

    fn get(&self, path: &str) -> Result<reqwest::blocking::Response, reqwest::Error> {
        let url = self.base_url.join(path).unwrap();
        let response = self.client.get(url).send();
        response
    }

    fn post(
        &self,
        path: &str,
        body: String,
    ) -> Result<reqwest::blocking::Response, reqwest::Error> {
        let url = self.base_url.join(path).unwrap();
        let response = self.client.post(url).body(body).send();
        response
    }

    fn delete(&self, path: &str) -> Result<reqwest::blocking::Response, reqwest::Error> {
        let url = self.base_url.join(path).unwrap();
        let response = self.client.delete(url).send();
        response
    }

    pub fn get_reminders(&self) -> Result<Vec<Reminder>, OyeClientError> {
        let body = match self.get("reminder") {
            Ok(response) => {
                let status = response.status();
                let body = match response.text() {
                    Ok(body) => body,
                    Err(_) => {
                        return Err(OyeClientError::FailedToGetReminders(format!(
                            "failed to get body from API response - response status code: {}",
                            status
                        )));
                    }
                };
                if status.is_client_error() || status.is_server_error() {
                    let failed_response: GetRemindersFailedResponse =
                        serde_jsonrc::from_str(&body).unwrap();
                    return Err(OyeClientError::FailedToGetReminders(
                        failed_response.message,
                    ));
                }
                body
            }
            Err(error) => return Err(OyeClientError::FailedToGetReminders(error.to_string())),
        };

        let payload: GetRemindersSuccessfulResponse = match serde_jsonrc::from_str(&body) {
            Ok(payload) => payload,
            Err(error) => return Err(OyeClientError::FailedToGetReminders(error.to_string())),
        };

        Ok(payload.reminders)
    }

    pub fn create_reminder(&self, utterance: Utterance) -> Result<Reminder, OyeClientError> {
        let payload = CreateReminderRequestPayload { utterance };
        let body = match self.post("reminder", serde_jsonrc::to_string(&payload).unwrap()) {
            Ok(response) => {
                let status = response.status();
                let body = match response.text() {
                    Ok(body) => body,
                    Err(_) => {
                        return Err(OyeClientError::FailedToCreateReminder(format!(
                            "failed to get body from API response - response status code: {}",
                            status
                        )));
                    }
                };
                if status.is_client_error() || status.is_server_error() {
                    let failed_response: CreateRemindersFailedResponse =
                        serde_jsonrc::from_str(&body).unwrap();
                    return Err(OyeClientError::FailedToCreateReminder(
                        failed_response.message,
                    ));
                }
                body
            }
            Err(error) => return Err(OyeClientError::FailedToCreateReminder(error.to_string())),
        };

        let response_payload: CreateRemindersResponse = match serde_jsonrc::from_str(&body) {
            Ok(payload) => payload,
            Err(error) => return Err(OyeClientError::FailedToCreateReminder(error.to_string())),
        };

        Ok(response_payload.added_reminder)
    }

    pub fn delete_reminder(&self, reminder_id: ReminderId) -> Result<Reminder, OyeClientError> {
        let path = format!("reminder/{}", reminder_id);
        let body = match self.delete(&path) {
            Ok(response) => {
                let status = response.status();
                let body = match response.text() {
                    Ok(body) => body,
                    Err(_) => {
                        return Err(OyeClientError::FailedToDeleteReminder(format!(
                            "failed to get body from API response - response status code: {}",
                            status
                        )))
                    }
                };
                body
            }
            Err(error) => return Err(OyeClientError::FailedToDeleteReminder(error.to_string())),
        };

        let response_payload: DeleteRemindersResponse = match serde_jsonrc::from_str(&body) {
            Ok(payload) => payload,
            Err(error) => {
                return Err(OyeClientError::FailedToDeleteReminder(format!(
                    "could not parse response payload. Reason: {}. Response: {}",
                    error.to_string(),
                    body
                )))
            }
        };

        Ok(response_payload.deleted_reminder)
    }
}

pub type ReminderId = String;
pub type ReminderDescription = String;
pub type Utterance = String;

#[derive(Debug, Deserialize)]
pub struct Reminder {
    pub id: ReminderId,
    pub description: ReminderDescription,
}

#[derive(Debug, Deserialize)]
struct GetRemindersSuccessfulResponse {
    reminders: Vec<Reminder>,
}

#[derive(Debug, Deserialize)]
struct GetRemindersFailedResponse {
    message: String,
}

#[derive(Debug, Serialize)]
struct CreateReminderRequestPayload {
    utterance: Utterance,
}

#[derive(Debug, Deserialize)]
struct CreateRemindersResponse {
    added_reminder: Reminder,
}

#[derive(Debug, Deserialize)]
struct CreateRemindersFailedResponse {
    message: String,
}

#[derive(Debug, Deserialize)]
struct DeleteRemindersResponse {
    deleted_reminder: Reminder,
}

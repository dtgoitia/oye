use chrono::Local;
use std::collections::HashMap;

use crate::{
    config::Config,
    exit_with_error,
    oye::{IsoTimezone, OyeClient, Reminder, ReminderId},
};

pub fn list_all_reminders(config: &Config) -> () {
    let client = OyeClient::new(&config);

    let reminders = match client.get_reminders() {
        Ok(reminders) => reminders,
        Err(error) => {
            return exit_with_error(format!("failed to list reminders, reason: {:?}", error))
        }
    };
    if reminders.is_empty() {
        println!("There are no reminders");
        return;
    }

    println!("Reminders:");

    reminders
        .iter()
        .enumerate()
        .map(|(n, reminder)| format!("{}  {}", n + 1, reminder.description))
        .for_each(|reminder| println!("  {}", reminder));
}

fn input(message: &str) -> String {
    let mut answer = String::new();
    println!("{}", message);
    std::io::stdin().read_line(&mut answer).unwrap();
    answer
}

pub fn create_reminder(config: &Config) -> () {
    let utterance = input("Type reminder:");

    let timezone = get_local_timezone();

    let client = OyeClient::new(&config);
    match client.create_reminder(utterance, timezone) {
        Ok(reminder) => println!("Reminder successfully created, reminder={:?}", reminder),
        Err(error) => {
            return exit_with_error(format!("failed to add reminder, reason: {:?}", error))
        }
    };
}

fn are_indexes_valid(
    available: &HashMap<SelectableReminderNumber, ReminderId>,
    selected: &Vec<SelectableReminderNumber>,
) -> Result<(), SelectableReminderNumber> {
    for selected in selected {
        if available.contains_key(selected) == false {
            return Err(selected.clone());
        }
    }

    return Ok(());
}

type SelectedReminderNumber = String;
type SelectableReminderNumber = String;

fn ask_user_to_select_reminders(reminders: Vec<Reminder>) -> Vec<ReminderId> {
    let mut available: HashMap<SelectableReminderNumber, ReminderId> = HashMap::new();

    println!("Available reminders:");
    reminders.iter().enumerate().for_each(|(n, reminder)| {
        let reminder_number = (n + 1).to_string();
        available.insert(reminder_number.clone(), reminder.id.clone());
        println!("  {}  {}", reminder_number, reminder.description)
    });

    println!("Input the remiders you want to delete. Separate them by spaces if you want to delete many.");
    loop {
        let answer = input("Reminders to delete:").trim().to_string();
        let selected: Vec<SelectedReminderNumber> = answer
            .split(" ")
            .map(|n| n.to_string())
            .filter(|n| n != "")
            .collect();

        if selected.is_empty() {
            println!("You've selected nothing, please input numbers separated by spaces");
            continue;
        }

        match are_indexes_valid(&available, &selected) {
            Ok(()) => (),
            Err(first_invalid_selection) => {
                println!(
                    "{} is not a valid selection, please input numbers from the available list above",
                    first_invalid_selection
                );
                continue;
            }
        }

        let reminder_ids = selected
            .into_iter()
            .map(|index| available.get(&index))
            .map(|index| index.unwrap().to_string())
            .collect();

        return reminder_ids;
    }
}

pub fn delete_reminder_interactive(config: &Config) -> () {
    let client = OyeClient::new(&config);

    let reminders = client.get_reminders().expect("failed to get reminders!");
    if reminders.is_empty() {
        println!("There are no reminders to delete");
        return;
    }

    let selected = ask_user_to_select_reminders(reminders);

    for reminder_id in selected {
        match client.delete_reminder(reminder_id.clone()) {
            Ok(deleted_reminder) => println!(
                "Successfully deleted reminder {}: {}",
                deleted_reminder.id, deleted_reminder.description
            ),
            Err(error) => {
                return exit_with_error(format!(
                    "failed to delete reminder {}, reason: {:?}",
                    reminder_id, error
                ))
            }
        };
    }
    // TODO: call API
}

fn get_local_timezone() -> IsoTimezone {
    let mut iso_t = Local::now().to_rfc3339();

    // drop all chars but the last 6 ones
    let len = iso_t.len() - 6;
    iso_t.drain(0..len);

    iso_t.to_string()
}

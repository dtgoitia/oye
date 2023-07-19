use clap::Command;
use std::process;

mod config;
mod oye;
mod use_cases;

fn exit_with_error(message: String) -> () {
    println!("ERROR: {}", message);
    process::exit(1);
}

fn main() {
    let config = match config::get_config() {
        Ok(config) => config,
        Err(error) => {
            return exit_with_error(error.reason);
        }
    };

    let matches = Command::new("oye")
        .subcommand(Command::new("add").about("add a new reminder"))
        .subcommand(Command::new("list").about("show all reminders"))
        .subcommand(Command::new("delete").about("delete a reminder interactively"))
        .get_matches();

    match matches.subcommand() {
        Some(("add", _)) => use_cases::create_reminder(&config),
        Some(("list", _)) => use_cases::list_all_reminders(&config),
        Some(("delete", _)) => use_cases::delete_reminder_interactive(&config),
        _ => println!("other..."),
    }
}

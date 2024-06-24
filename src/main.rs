use std::{collections::HashMap, fs::File};

use serde::{Deserialize, Serialize};
use serde_json;

#[derive(Serialize, Deserialize, Debug)]
pub struct JsonData {
    libraries: Vec<String>,
    relations: HashMap<u32, Vec<u32>>,
}

fn main() -> anyhow::Result<()> {
    let file = File::open("sample/generated.json")?;
    let json_data: JsonData = serde_json::from_reader(file)?;
    println!("{:?}", json_data);
    Ok(())
}

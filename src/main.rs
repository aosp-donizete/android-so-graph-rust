use petgraph::{
    graph::NodeIndex,
    stable_graph::{StableDiGraph, StableGraph},
};
use std::{collections::HashMap, fs::File};

use egui_graphs::{Graph, GraphView};
use serde::{Deserialize, Serialize};
use serde_json;

#[derive(Serialize, Deserialize, Debug)]
pub struct JsonData {
    libraries: Vec<String>,
    relations: HashMap<u32, Vec<u32>>,
}

impl JsonData {
    fn new() -> Self {
        let file = File::open("sample/generated.json").unwrap();
        serde_json::from_reader(file).unwrap()
    }
}

fn generate_graph() -> StableGraph<(), ()> {
    let mut graph: StableGraph<(), ()> = StableDiGraph::new();
    let mut nodes = Vec::<NodeIndex>::new();
    let json_data = JsonData::new();

    for (index, value) in json_data.libraries.iter().enumerate() {
        let node = graph.add_node(());
        nodes.insert(index, node);
    }

    for (node_index, relations_indexes) in json_data.relations.iter() {
        let node = nodes.get(*node_index as usize).unwrap();
        for relation_index in relations_indexes {
            let relation_node = nodes.get(*relation_index as usize).unwrap();
            graph.add_edge(*node, *relation_node, ());
        }
    }

    graph
}

pub struct BasicApp {
    g: Graph<(), ()>,
}

impl BasicApp {
    fn new(_: &eframe::CreationContext<'_>) -> Self {
        let g = generate_graph();
        Self { g: Graph::from(&g) }
    }
}

impl eframe::App for BasicApp {
    fn update(&mut self, ctx: &egui::Context, _: &mut eframe::Frame) {
        egui::CentralPanel::default().show(ctx, |ui| {
            ui.add(&mut GraphView::<_, _, _>::new(&mut self.g));
        });
    }
}

fn main() -> anyhow::Result<()> {
    let native_options = eframe::NativeOptions::default();
    eframe::run_native(
        "egui_graphs_basic_demo",
        native_options,
        Box::new(|cc| Box::new(BasicApp::new(cc))),
    )
    .unwrap();
    Ok(())
}

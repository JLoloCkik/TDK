use actix_cors::Cors;
use actix_web::{web, App, HttpResponse, HttpServer, Responder};
use serde::{Deserialize, Serialize};

// Beemeljük a másik két fájlt mod-ként
mod calculator;
mod ai;

#[derive(Deserialize)]
struct CalcReq { a: f64, b: f64, operator: String }

#[derive(Serialize)]
struct CalcRes { result: String }

#[derive(Deserialize)]
struct AiReq { text: String }

async fn calc_endpoint(req: web::Json<CalcReq>) -> impl Responder {
    let res = calculator::calculate(req.a, req.b, &req.operator);
    HttpResponse::Ok().json(CalcRes { result: res })
}

async fn ai_endpoint(req: web::Json<AiReq>) -> impl Responder {
    let text = req.text.clone();

    tokio::spawn(async move {
        ai::run_ai_task(text).await;
    });

    HttpResponse::Ok().json(serde_json::json!({"success": true}))
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    println!("🦀 Rust Backend fut a 5001-es porton!");
    HttpServer::new(|| {
        App::new()
            .wrap(Cors::permissive())
            .route("/api/calculate", web::post().to(calc_endpoint))
            .route("/api/ai", web::post().to(ai_endpoint))
    })
    .bind(("127.0.0.1", 5001))?
    .run()
    .await
}
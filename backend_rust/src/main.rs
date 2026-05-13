use actix_cors::Cors;
use actix_web::{
    web,
    App,
    HttpResponse,
    HttpServer,
    Responder,
};

use serde::{Deserialize, Serialize};

mod ai;
mod calculator;

#[derive(Deserialize)]
struct SqrtReq { a: f64 }
struct CalcReq {
    a: f64,
    b: f64,
    operator: String,
}

#[derive(Serialize)]
struct CalcRes {
    result: String,
}

#[derive(Deserialize)]
struct AiReq {
    text: String,
}

async fn calc_endpoint(
    req: web::Json<CalcReq>
) -> impl Responder {

    let result = calculator::calculate(
        req.a,
        req.b,
        &req.operator
    );

    HttpResponse::Ok().json(
        CalcRes { result }
    )
}

async fn ai_endpoint(
    req: web::Json<AiReq>
) -> impl Responder {

    let text = req.text.clone();

    tokio::spawn(async move {
        ai::run_ai_task(text).await;
    });

    HttpResponse::Ok().json(
        serde_json::json!({
            "success": true
        })
    )
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {

    println!("Rust backend fut: 5001");

    HttpServer::new(|| {

        App::new()
            .wrap(Cors::permissive())

            .route(
                "/api/calculate",
                web::post().to(calc_endpoint)
            )

            .route(
                "/api/ai",
                web::post().to(ai_endpoint)
            )
    })

    .bind(("127.0.0.1", 5001))?

    .run()

    .await
}
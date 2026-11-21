#![forbid(unsafe_code)]

use std::io::{BufRead, BufReader, Read, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;

use stuff::publish::PublishError;
use stuff::publish::coordinator::Coordinator;
use stuff::publish::{Environment, Registry};

fn recorder() -> (Arc<Mutex<Vec<Duration>>>, impl Fn(Duration) + Send + Sync + 'static) {
    let slept = Arc::new(Mutex::new(Vec::new()));
    let recorded = Arc::clone(&slept);
    (slept, move |duration| recorded.lock().unwrap().push(duration))
}

fn read_request(stream: &mut TcpStream) -> String {
    let mut reader = BufReader::new(stream.try_clone().unwrap());
    let mut line = String::new();
    reader.read_line(&mut line).unwrap();
    let path = line.split_whitespace().nth(1).unwrap().to_string();
    let mut length = 0;
    loop {
        line.clear();
        reader.read_line(&mut line).unwrap();
        if line == "\r\n" {
            break;
        }
        if let Some((name, value)) = line.split_once(':')
            && name.eq_ignore_ascii_case("content-length")
        {
            length = value.trim().parse().unwrap();
        }
    }
    let mut body = vec![0; length];
    reader.read_exact(&mut body).unwrap();
    path
}

fn reply(stream: &mut TcpStream, status: u16, retry_after: Option<&str>, body: &str) {
    let retry = retry_after.map(|value| format!("retry-after: {value}\r\n")).unwrap_or_default();
    write!(stream, "HTTP/1.1 {status} Service Unavailable\r\ncontent-type: application/json\r\n{retry}content-length: {}\r\nconnection: close\r\n\r\n{body}", body.len()).unwrap();
}

fn coordinator(endpoint: String, window: Duration, sleeper: impl Fn(Duration) + Send + Sync + 'static) -> Coordinator {
    let env = Environment::from_pairs([
        ("STUFF_COORDINATOR_URL", endpoint),
        ("STUFF_COORDINATOR_TOKEN", "service".to_string()),
        ("STUFF_S3_ACCESS_KEY_ID", "service".to_string()),
        ("STUFF_S3_SECRET_ACCESS_KEY", "secret".to_string()),
    ]);
    Coordinator::configured(&env, Registry::Cargo)
        .expect("publishing service configuration")
        .expect("configured coordinator")
        .with_retry_window(window)
        .with_sleeper(sleeper)
}

#[test]
fn begin_retries_a_frozen_response_honoring_retry_after() {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let endpoint = format!("http://{}", listener.local_addr().unwrap());
    let (sleeps, sleeper) = recorder();
    let server = thread::spawn(move || {
        for index in 0..3 {
            let (mut socket, _) = listener.accept().unwrap();
            let path = read_request(&mut socket);
            if index < 2 {
                assert_eq!(path, "/_publication/cargo/begin");
            } else {
                assert_eq!(path, "/_publication/cargo/abort");
            }
            if index == 0 {
                reply(&mut socket, 503, Some("2"), r#"{"error":"frozen"}"#);
            } else {
                reply(&mut socket, 200, None, r#"{"token":"lease-1","revision":7,"expires":100}"#);
            }
        }
    });
    let coordinator = coordinator(endpoint, Duration::from_secs(15 * 60), sleeper);
    let lease = coordinator.begin().expect("retried begin");
    assert_eq!(lease.token, "lease-1");
    assert_eq!(lease.revision, 7);
    assert_eq!(*sleeps.lock().unwrap(), vec![Duration::from_secs(2)]);
    drop(lease);
    server.join().unwrap();
}

#[test]
fn frozen_retries_stop_after_the_total_window() {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let endpoint = format!("http://{}", listener.local_addr().unwrap());
    let (sleeps, sleeper) = recorder();
    let server = thread::spawn(move || {
        for _ in 0..3 {
            let (mut socket, _) = listener.accept().unwrap();
            assert_eq!(read_request(&mut socket), "/_publication/cargo/begin");
            reply(&mut socket, 503, Some("60"), r#"{"error":"frozen"}"#);
        }
    });
    let coordinator = coordinator(endpoint, Duration::from_secs(120), sleeper);
    let error = coordinator.begin().err().expect("frozen retries exhaust the window");
    assert!(matches!(&error, PublishError::Transport(_)), "{error}");
    assert_eq!(*sleeps.lock().unwrap(), vec![Duration::from_secs(60), Duration::from_secs(60)]);
    server.join().unwrap();
}

#[test]
fn retry_after_is_capped_at_sixty_seconds() {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let endpoint = format!("http://{}", listener.local_addr().unwrap());
    let (sleeps, sleeper) = recorder();
    let server = thread::spawn(move || {
        for _ in 0..2 {
            let (mut socket, _) = listener.accept().unwrap();
            assert_eq!(read_request(&mut socket), "/_publication/cargo/begin");
            reply(&mut socket, 503, Some("600"), r#"{"error":"frozen"}"#);
        }
    });
    let coordinator = coordinator(endpoint, Duration::from_secs(60), sleeper);
    let error = coordinator.begin().err().expect("oversized retry-after is capped");
    assert!(matches!(&error, PublishError::Transport(_)), "{error}");
    assert_eq!(*sleeps.lock().unwrap(), vec![Duration::from_secs(60)]);
    server.join().unwrap();
}

#[test]
fn other_statuses_fail_without_retrying() {
    for (status, expected) in [(500, false), (409, true)] {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let endpoint = format!("http://{}", listener.local_addr().unwrap());
        let (sleeps, sleeper) = recorder();
        let server = thread::spawn(move || {
            let (mut socket, _) = listener.accept().unwrap();
            assert_eq!(read_request(&mut socket), "/_publication/cargo/begin");
            reply(&mut socket, status, Some("1"), r#"{"error":"unavailable"}"#);
        });
        let coordinator = coordinator(endpoint, Duration::from_secs(15 * 60), sleeper);
        let error = coordinator.begin().err().expect("non-503 status fails");
        assert_eq!(matches!(&error, PublishError::Conflict(_)), expected, "{error}");
        assert!(sleeps.lock().unwrap().is_empty(), "status {status} must not sleep");
        server.join().unwrap();
    }
}

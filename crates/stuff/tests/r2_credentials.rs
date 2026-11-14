#![forbid(unsafe_code)]

mod support;

use std::fs;
use std::process::Command;
use stuff::publish::r2::credentials::resolve;
use stuff::publish::{Environment, ExitCode};
use support::write_executable;

#[test]
fn missing_or_partial_credentials_never_invoke_cloudflare() {
    let directory = tempfile::tempdir().unwrap();
    let marker = directory.path().join("cf-called");
    let program = directory.path().join("cf");
    write_executable(&program, &format!("#!/bin/sh\ntouch '{}'\nexit 99\n", marker.display()));
    for partial in [false, true] {
        let mut pairs = vec![("STUFF_CONFIG_HOME", directory.path().to_str().unwrap()), ("PATH", directory.path().to_str().unwrap())];
        if partial { pairs.push(("R2_S3_ENDPOINT", "https://maintenance.invalid")); }
        let error = resolve(&Environment::from_pairs(pairs), "stuff-mycrates").unwrap_err();
        assert_eq!(error.classification(), ExitCode::Usage);
        assert!(!marker.exists());
        assert!(!error.to_string().contains("cf auth"));
    }
}

#[test]
fn native_credentials_use_the_owner_service_file_before_backend_environment() {
    let directory = tempfile::tempdir().unwrap();
    let path = directory.path().join("credentials.json");
    fs::write(&path, r#"{"schema":1,"endpoint":"https://stuff.example","coordinator_token":"manage","access_key_id":"service-key","secret_access_key":"service-secret","region":"auto"}"#).unwrap();
    #[cfg(unix)] {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&path, fs::Permissions::from_mode(0o600)).unwrap();
    }
    let env = Environment::from_pairs([
        ("STUFF_CONFIG_HOME", directory.path().to_str().unwrap()),
        ("R2_S3_ENDPOINT", "https://backend.invalid"),
        ("R2_S3_ACCESS_KEY_ID", "backend-key"),
        ("R2_S3_SECRET_ACCESS_KEY", "backend-secret"),
    ]);
    let credentials = resolve(&env, "stuff-mycrates").unwrap();
    assert_eq!(credentials.endpoint, "https://stuff.example/_s3");
    assert_eq!(credentials.access_key_id, "service-key");
    assert_eq!(credentials.secret_access_key, "service-secret");
    let output = Command::new(env!("CARGO_BIN_EXE_stuff")).args(["credentials", "stuff-mycrates"])
        .env_clear().env("STUFF_CONFIG_HOME", directory.path()).output().unwrap();
    assert!(output.status.success());
    let stdout = String::from_utf8(output.stdout).unwrap();
    assert!(stdout.contains("https://stuff.example/_s3"));
    assert!(!stdout.contains("manage"));
    assert!(!stdout.contains("backend"));
}

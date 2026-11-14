use crate::publish::{Environment, PublishError};

use super::client::Credentials;

pub fn resolve(env: &Environment, bucket: &str) -> Result<Credentials, PublishError> {
    if bucket.is_empty() {
        return Err(PublishError::Config("bucket is empty".into()));
    }
    if let Some(service) = crate::publish::service::PublishingService::configured(env)? {
        return Ok(Credentials {
            endpoint: format!("{}/_s3", service.endpoint),
            access_key_id: service.access_key_id, secret_access_key: service.secret_access_key,
            region: service.region, session_token: None,
        });
    }
    let names = ["R2_S3_ENDPOINT", "R2_S3_ACCESS_KEY_ID", "R2_S3_SECRET_ACCESS_KEY"];
    if names.iter().any(|name| env.get(name).is_some()) {
        if !names.iter().all(|name| env.non_empty(name).is_some()) {
            return Err(PublishError::Config("explicit maintenance S3 credentials require all three endpoint, access key and secret key values".into()));
        }
        return Credentials::from_env(|name| env.get(name).map(str::to_string));
    }
    Err(PublishError::Config("publishing service credentials are required; configure stuff/credentials.json".into()))
}

pub fn shell_exports(env: &Environment, bucket: &str) -> Result<String, PublishError> {
    let credentials = resolve(env, bucket)?;
    let mut lines = vec![
        ("R2_S3_ENDPOINT", credentials.endpoint),
        ("R2_S3_ACCESS_KEY_ID", credentials.access_key_id),
        ("R2_S3_SECRET_ACCESS_KEY", credentials.secret_access_key),
    ];
    if let Some(token) = credentials.session_token {
        lines.push(("R2_S3_SESSION_TOKEN", token));
    }
    Ok(lines
        .into_iter()
        .map(|(name, value)| format!("export {name}='{}'\n", value.replace('\'', "'\\''")))
        .collect())
}


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn coordinator_mode_requires_the_service_key_and_ignores_backend_credentials() {
        let missing = Environment::from_pairs([
            ("STUFF_COORDINATOR_URL", "http://127.0.0.1:8787"),
            ("R2_S3_ENDPOINT", "http://backend"),
            ("R2_S3_ACCESS_KEY_ID", "backend-key"),
            ("R2_S3_SECRET_ACCESS_KEY", "backend-secret"),
        ]);
        assert!(resolve(&missing, "bucket").is_err());
        let configured = Environment::from_pairs([
            ("STUFF_COORDINATOR_URL", "http://127.0.0.1:8787"),
            ("STUFF_S3_GATEWAY_URL", "http://127.0.0.1:8787/_s3"),
            ("STUFF_COORDINATOR_TOKEN", "service-token"),
            ("STUFF_S3_ACCESS_KEY_ID", "service-key"),
            ("STUFF_S3_SECRET_ACCESS_KEY", "service-secret"),
            ("R2_S3_ENDPOINT", "http://backend"),
            ("R2_S3_ACCESS_KEY_ID", "backend-key"),
            ("R2_S3_SECRET_ACCESS_KEY", "backend-secret"),
        ]);
        let credentials = resolve(&configured, "bucket").unwrap();
        assert_eq!(credentials.endpoint, "http://127.0.0.1:8787/_s3");
        assert_eq!(credentials.access_key_id, "service-key");
        assert_eq!(credentials.secret_access_key, "service-secret");
    }

    #[test]
    fn explicit_maintenance_credentials_resolve_without_external_tools() {
        let env = Environment::from_pairs([
            ("R2_S3_ENDPOINT", "https://account.r2.cloudflarestorage.com/"),
            ("R2_S3_ACCESS_KEY_ID", "access"),
            ("R2_S3_SECRET_ACCESS_KEY", "secret"),
            ("R2_S3_SESSION_TOKEN", "token"),
            ("PATH", "/nonexistent"),
        ]);
        let credentials = resolve(&env, "bucket").unwrap();
        assert_eq!(
            credentials,
            Credentials {
                endpoint: "https://account.r2.cloudflarestorage.com".to_string(),
                access_key_id: "access".to_string(),
                secret_access_key: "secret".to_string(),
                region: "auto".to_string(),
                session_token: Some("token".to_string()),
            }
        );
    }

    #[test]
    fn shell_exports_quote_values_for_eval() {
        let env = Environment::from_pairs([
            ("R2_S3_ENDPOINT", "https://account.r2.cloudflarestorage.com"),
            ("R2_S3_ACCESS_KEY_ID", "access"),
            ("R2_S3_SECRET_ACCESS_KEY", "se'cret"),
            ("STUFF_CONFIG_HOME", "/nonexistent"),
            ("PATH", "/nonexistent"),
        ]);
        assert_eq!(
            shell_exports(&env, "bucket").unwrap(),
            "export R2_S3_ENDPOINT='https://account.r2.cloudflarestorage.com'\n\
             export R2_S3_ACCESS_KEY_ID='access'\n\
             export R2_S3_SECRET_ACCESS_KEY='se'\\''cret'\n"
        );
    }

    #[test]
    fn partial_maintenance_credentials_fail_without_external_tools() {
        let env = Environment::from_pairs([("R2_S3_ENDPOINT", "https://example")]);
        let error = resolve(&env, "bucket").unwrap_err();
        assert!(error.to_string().contains("all three"), "{error}");
    }
}

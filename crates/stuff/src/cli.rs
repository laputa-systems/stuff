#![forbid(unsafe_code)]

use std::fmt::Write as _;

use crate::error::{Error, Result};
use crate::publish::{
    CargoPublish, MirrorPublish, NpmPublish, OciImage, OciSource, Options, PublishRequest,
    PypiPublish, PypiSpec, Registry, Request,
};

const OPT_PACKAGE: &str = "-p";
const OPT_VERSIONS: &str = "--versions";
const OPT_JSON: &str = "--json";
const OPT_SAMPLE_ARTIFACTS: &str = "--sample-artifacts";
const OPT_REGISTRY: &str = "--registry";
const OPT_CARGO_BASE: &str = "--cargo-base";
const OPT_NPM_BASE: &str = "--npm-base";
const OPT_PYPI_BASE: &str = "--pypi-base";
const OPT_OCI_BASE: &str = "--oci-base";
const OPT_MIRROR_BASE: &str = "--mirror-base";
const OPT_CARGO_DIR: &str = "--cargo-dir";
const OPT_NPM_DIR: &str = "--npm-dir";
const OPT_PYPI_DIR: &str = "--pypi-dir";
const OPT_OCI_DIR: &str = "--oci-dir";
const OPT_MIRROR_DIR: &str = "--mirror-dir";
const OPT_OUTPUT: &str = "--output";
const OPT_EXPECTED_GENERATION: &str = "--expected-generation";
const OPT_DRY_RUN: &str = "--dry-run";
const OPT_VERBOSE: &str = "--verbose";
const OPT_MANIFEST_PATH: &str = "--manifest-path";
const OPT_LOCKFILE: &str = "--lockfile";
const OPT_PROJECT: &str = "--project";
const OPT_TARBALL: &str = "--tarball";
const OPT_ALLOW_SDIST: &str = "--allow-sdist";
const OPT_WHEEL: &str = "--wheel";
const OPT_IMAGE: &str = "--image";
const OPT_LAYOUT: &str = "--layout";
const OPT_REPOSITORY: &str = "--repository";
const OPT_TAG: &str = "--tag";
const OPT_INVENTORY: &str = "--inventory";
const OPT_LOCK: &str = "--lock";
const OPT_MANIFEST: &str = "--manifest";
const OPT_ALLOW_DROPS: &str = "--allow-drops";

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RegistryFilter {
    Cargo,
    Npm,
    Pypi,
    Oci,
    Mirror,
}

impl RegistryFilter {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Cargo => Registry::Cargo,
            Self::Npm => Registry::Npm,
            Self::Pypi => Registry::Pypi,
            Self::Oci => Registry::Oci,
            Self::Mirror => Registry::Mirror,
        }.as_str()
    }

    pub fn parse(s: &str) -> Option<Self> {
        match Registry::parse(s)? {
            Registry::Cargo => Some(Self::Cargo),
            Registry::Npm => Some(Self::Npm),
            Registry::Pypi => Some(Self::Pypi),
            Registry::Oci => Some(Self::Oci),
            Registry::Mirror => Some(Self::Mirror),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Command {
    Ls,
    Search,
    Diff,
    Doctor,
    Render,
    Publish,
    Republish,
    Rollback,
    Credentials,
    LockPath,
}

impl Command {
    fn name(self) -> &'static str {
        match self {
            Command::Ls => "ls",
            Command::Search => "search",
            Command::Diff => "diff",
            Command::Doctor => "doctor",
            Command::Render => "render",
            Command::Publish => "publish",
            Command::Republish => "republish",
            Command::Rollback => "rollback",
            Command::Credentials => "credentials",
            Command::LockPath => "lock-path",
        }
    }

    fn parse(name: &str) -> Option<Self> {
        [Self::Ls, Self::Search, Self::Diff, Self::Doctor, Self::Render, Self::Publish,
         Self::Republish, Self::Rollback, Self::Credentials, Self::LockPath]
            .into_iter().find(|command| command.name() == name)
    }

    fn allowed_flags(self) -> AllowedFlags {
        match self {
            Command::Ls => AllowedFlags {
                registry: true,
                versions: true,
                json: true,
                base_urls: true,
                local_dirs: true,
                ..AllowedFlags::default()
            },
            Command::Search => AllowedFlags {
                registry: true,
                json: true,
                base_urls: true,
                local_dirs: true,
                ..AllowedFlags::default()
            },
            Command::Diff => AllowedFlags { json: true, ..AllowedFlags::default() },
            Command::Doctor => AllowedFlags {
                registry: true,
                sample_artifacts: true,
                base_urls: true,
                local_dirs: true,
                expected_generation: true,
                ..AllowedFlags::default()
            },
            Command::Render => AllowedFlags {
                registry: true,
                base_urls: true,
                local_dirs: true,
                output: true,
                ..AllowedFlags::default()
            },
            Command::Publish
            | Command::Republish
            | Command::Rollback
            | Command::Credentials
            | Command::LockPath => {
                AllowedFlags::default()
            }
        }
    }
}

#[derive(Clone, Copy, Default)]
struct AllowedFlags {
    registry: bool,
    versions: bool,
    json: bool,
    sample_artifacts: bool,
    base_urls: bool,
    local_dirs: bool,
    output: bool,
    expected_generation: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Parsed {
    pub command: Command,
    pub registry: Option<RegistryFilter>,
    pub versions: bool,
    pub json: bool,
    pub sample_artifacts: bool,
    pub cargo_base: Option<String>,
    pub npm_base: Option<String>,
    pub pypi_base: Option<String>,
    pub oci_base: Option<String>,
    pub mirror_base: Option<String>,
    pub cargo_dir: Option<String>,
    pub npm_dir: Option<String>,
    pub pypi_dir: Option<String>,
    pub oci_dir: Option<String>,
    pub mirror_dir: Option<String>,
    pub output: Option<String>,
    pub expected_generation: Option<String>,
    pub positionals: Vec<String>,
    pub request: Option<Request>,
}

impl Parsed {
    pub fn registry_filter(&self) -> Option<&'static str> {
        self.registry.map(|r| r.as_str())
    }
}

fn usage_error(detail: impl Into<String>) -> Error {
    Error::usage(detail)
}

fn ensure_allowed(command: Command, flag: &str, present: bool, allowed: bool) -> Result<()> {
    if present && !allowed {
        return Err(usage_error(format!("{} does not take {flag}", command.name())));
    }
    Ok(())
}

pub fn parse_args(argv: &[String]) -> Result<Parsed> {
    match argv.first().and_then(|name| Command::parse(name)) {
        Some(Command::Publish) => parse_publish(&argv[1..]),
        Some(Command::Republish) => parse_republish(&argv[1..]),
        Some(Command::Rollback) => parse_rollback(&argv[1..]),
        Some(Command::Credentials) => parse_bucket(Command::Credentials, &argv[1..]),
        Some(Command::LockPath) => parse_lock_path(&argv[1..]),
        _ => parse_read_only(argv),
    }
}

fn parse_read_only(argv: &[String]) -> Result<Parsed> {
    let mut args = argv.iter().peekable();
    let command = match args.next() {
        Some(name) => Command::parse(name).ok_or_else(|| usage_error(format!("unknown command '{name}'")))?,
        None => return Err(usage_error("a command is required")),
    };
    let mut parsed = Parsed {
        command,
        registry: None,
        versions: false,
        json: false,
        sample_artifacts: false,
        cargo_base: None,
        npm_base: None,
        pypi_base: None,
        oci_base: None,
        mirror_base: None,
        cargo_dir: None,
        npm_dir: None,
        pypi_dir: None,
        oci_dir: None,
        mirror_dir: None,
        output: None,
        expected_generation: None,
        positionals: Vec::new(),
        request: None,
    };
    let mut seen_registry = false;
    while let Some(arg) = args.next() {
        match arg.as_str() {
            OPT_VERSIONS => parsed.versions = true,
            OPT_JSON => parsed.json = true,
            OPT_SAMPLE_ARTIFACTS => parsed.sample_artifacts = true,
            OPT_REGISTRY => {
                let value = args.next().ok_or_else(|| usage_error("--registry requires a value"))?;
                if seen_registry {
                    return Err(usage_error("--registry may only be specified once"));
                }
                seen_registry = true;
                parsed.registry = Some(
                    RegistryFilter::parse(value).ok_or_else(|| usage_error(format!("unsupported registry '{value}'")))?,
                );
            }
            OPT_CARGO_BASE | OPT_NPM_BASE | OPT_PYPI_BASE | OPT_OCI_BASE | OPT_MIRROR_BASE | OPT_CARGO_DIR | OPT_NPM_DIR
            | OPT_PYPI_DIR | OPT_OCI_DIR | OPT_MIRROR_DIR | OPT_OUTPUT | OPT_EXPECTED_GENERATION => {
                let value = args.next().ok_or_else(|| usage_error(format!("{arg} requires a value")))?;
                let slot = match arg.as_str() {
                    OPT_CARGO_BASE => &mut parsed.cargo_base,
                    OPT_NPM_BASE => &mut parsed.npm_base,
                    OPT_PYPI_BASE => &mut parsed.pypi_base,
                    OPT_OCI_BASE => &mut parsed.oci_base,
                    OPT_MIRROR_BASE => &mut parsed.mirror_base,
                    OPT_CARGO_DIR => &mut parsed.cargo_dir,
                    OPT_NPM_DIR => &mut parsed.npm_dir,
                    OPT_PYPI_DIR => &mut parsed.pypi_dir,
                    OPT_OCI_DIR => &mut parsed.oci_dir,
                    OPT_MIRROR_DIR => &mut parsed.mirror_dir,
                    OPT_OUTPUT => &mut parsed.output,
                    _ => &mut parsed.expected_generation,
                };
                if slot.is_some() {
                    return Err(usage_error(format!("{arg} may only be specified once")));
                }
                *slot = Some(value.clone());
            }
            other if other.starts_with('-') => return Err(usage_error(format!("unknown option: {other}"))),
            other => parsed.positionals.push(other.to_string()),
        }
    }
    let allowed = parsed.command.allowed_flags();
    for (flag, present, allowed) in [
        (OPT_REGISTRY, parsed.registry.is_some(), allowed.registry),
        (OPT_VERSIONS, parsed.versions, allowed.versions),
        (OPT_JSON, parsed.json, allowed.json),
        (OPT_SAMPLE_ARTIFACTS, parsed.sample_artifacts, allowed.sample_artifacts),
        (OPT_CARGO_BASE, parsed.cargo_base.is_some(), allowed.base_urls),
        (OPT_NPM_BASE, parsed.npm_base.is_some(), allowed.base_urls),
        (OPT_PYPI_BASE, parsed.pypi_base.is_some(), allowed.base_urls),
        (OPT_OCI_BASE, parsed.oci_base.is_some(), allowed.base_urls),
        (OPT_MIRROR_BASE, parsed.mirror_base.is_some(), allowed.base_urls),
        (OPT_CARGO_DIR, parsed.cargo_dir.is_some(), allowed.local_dirs),
        (OPT_NPM_DIR, parsed.npm_dir.is_some(), allowed.local_dirs),
        (OPT_PYPI_DIR, parsed.pypi_dir.is_some(), allowed.local_dirs),
        (OPT_OCI_DIR, parsed.oci_dir.is_some(), allowed.local_dirs),
        (OPT_MIRROR_DIR, parsed.mirror_dir.is_some(), allowed.local_dirs),
        (OPT_OUTPUT, parsed.output.is_some(), allowed.output),
        (
            OPT_EXPECTED_GENERATION,
            parsed.expected_generation.is_some(),
            allowed.expected_generation,
        ),
    ] {
        ensure_allowed(parsed.command, flag, present, allowed)?;
    }
    match parsed.command {
        Command::Ls | Command::Doctor | Command::Render => {
            if !parsed.positionals.is_empty() {
                return Err(usage_error(format!(
                    "{} does not take positional arguments",
                    parsed.command.name()
                )));
            }
        }
        Command::Search => {
            if parsed.positionals.len() != 1 {
                return Err(usage_error("search requires exactly one query"));
            }
        }
        Command::Diff => {
            if parsed.positionals.len() != 2 {
                return Err(usage_error("diff requires two catalog paths"));
            }
        }
        Command::Publish
            | Command::Republish
            | Command::Rollback
            | Command::Credentials
            | Command::LockPath => {}
    }
    Ok(parsed)
}

fn parse_bucket(command: Command, args: &[String]) -> Result<Parsed> {
    match args {
        [bucket] if !bucket.is_empty() && !bucket.starts_with('-') => Ok(Parsed {
            positionals: vec![bucket.clone()],
            ..request_parsed(command, None)
        }),
        _ => Err(usage_error(format!("{} requires exactly one bucket", command.name()))),
    }
}

fn parse_lock_path(args: &[String]) -> Result<Parsed> {
    match args {
        [flag, name] if flag == OPT_REGISTRY => {
            let registry = RegistryFilter::parse(name)
                .ok_or_else(|| usage_error(format!("unknown registry: {name}")))?;
            Ok(Parsed {
                registry: Some(registry),
                ..request_parsed(Command::LockPath, None)
            })
        }
        _ => parse_bucket(Command::LockPath, args),
    }
}

fn request_parsed(command: Command, request: impl Into<Option<Request>>) -> Parsed {
    Parsed {
        command,
        registry: None,
        versions: false,
        json: false,
        sample_artifacts: false,
        cargo_base: None,
        npm_base: None,
        pypi_base: None,
        oci_base: None,
        mirror_base: None,
        cargo_dir: None,
        npm_dir: None,
        pypi_dir: None,
        oci_dir: None,
        mirror_dir: None,
        output: None,
        expected_generation: None,
        positionals: Vec::new(),
        request: request.into(),
    }
}

fn publish_registry(args: &[String], command: &str) -> Result<(Registry, usize)> {
    match args.first().map(String::as_str) {
        Some(name) => {
            let registry = Registry::parse(name)
                .ok_or_else(|| usage_error(format!("unsupported {command} registry '{name}'")))?;
            Ok((registry, 1))
        }
        None => Err(usage_error(format!(
            "{command} requires a registry: cargo, npm, pypi, oci, or mirror"
        ))),
    }
}

fn next_value<'a>(args: &'a [String], index: &mut usize, flag: &str) -> Result<&'a str> {
    *index += 1;
    args.get(*index)
        .map(String::as_str)
        .ok_or_else(|| usage_error(format!("{flag} requires a value")))
}

fn assign_once(slot: &mut Option<String>, flag: &str, value: &str) -> Result<()> {
    if slot.is_some() {
        return Err(usage_error(format!("{flag} may only be specified once")));
    }
    *slot = Some(value.to_string());
    Ok(())
}

fn take_common_option(arg: &str, options: &mut Options) -> bool {
    match arg {
        OPT_DRY_RUN => options.dry_run = true,
        OPT_JSON => options.json = true,
        OPT_VERBOSE => options.verbose = true,
        _ => return false,
    }
    true
}

fn check_publish_option(command: Command, registry: Option<Registry>, arg: &str) -> Result<()> {
    if arg.starts_with('-') {
        let spec = HELP_COMMANDS.iter().find(|entry| entry.command == command && entry.registry == registry).unwrap();
        if !command_options(spec).contains(&arg) {
            return Err(usage_error(format!("unknown option: {arg}")));
        }
    }
    Ok(())
}

fn parse_publish(args: &[String]) -> Result<Parsed> {
    let (registry, mut index) = publish_registry(args, "publish")?;
    let (request, options) = match registry {
        Registry::Cargo => parse_cargo_publish(args, &mut index)?,
        Registry::Npm => {
            parse_npm_publish(args, &mut index)?
        }
        Registry::Pypi => parse_pypi_publish(args, &mut index)?,
        Registry::Oci => {
            let (oci, options) = parse_oci_publish(args, &mut index)?;
            (PublishRequest::Oci(oci), options)
        }
        Registry::Mirror => {
            let (mirror, options) = parse_mirror_publish(args, &mut index)?;
            (PublishRequest::Mirror(mirror), options)
        }
    };
    Ok(request_parsed(Command::Publish, Request::Publish { request, options }))
}

fn parse_cargo_publish(args: &[String], index: &mut usize) -> Result<(PublishRequest, Options)> {
    let mut cargo = CargoPublish { packages: Vec::new(), manifest_path: None, registry: None };
    let mut lockfiles = Vec::new();
    let mut options = Options::default();
    let mut seen_common: Vec<&str> = Vec::new();
    while *index < args.len() {
        let arg = args[*index].as_str();
        check_publish_option(Command::Publish, Some(Registry::Cargo), arg)?;
        if matches!(arg, OPT_DRY_RUN | OPT_JSON | OPT_VERBOSE) {
            if seen_common.contains(&arg) {
                return Err(usage_error(format!("{arg} may only be specified once")));
            }
            seen_common.push(arg);
            take_common_option(arg, &mut options);
            *index += 1;
            continue;
        }
        match arg {
            OPT_PACKAGE => {
                let value = next_value(args, index, OPT_PACKAGE)?;
                if value.is_empty() {
                    return Err(usage_error("-p requires a package name"));
                }
                cargo.packages.push(value.to_string());
            }
            OPT_MANIFEST_PATH => {
                let value = next_value(args, index, OPT_MANIFEST_PATH)?;
                assign_once(&mut cargo.manifest_path, OPT_MANIFEST_PATH, value)?;
            }
            OPT_REGISTRY => {
                let value = next_value(args, index, OPT_REGISTRY)?;
                assign_once(&mut cargo.registry, OPT_REGISTRY, value)?;
            }
            OPT_LOCKFILE => {
                let value = next_value(args, index, OPT_LOCKFILE)?;
                if value.is_empty() {
                    return Err(usage_error("--lockfile requires a path"));
                }
                lockfiles.push(value.to_string());
            }
            other if other.starts_with('-') => {
                return Err(usage_error(format!("unknown option: {other}")));
            }
            other => {
                return Err(usage_error(format!(
                    "publish cargo does not take positional argument '{other}'"
                )));
            }
        }
        *index += 1;
    }
    if !lockfiles.is_empty() {
        if !cargo.packages.is_empty() || cargo.manifest_path.is_some() || cargo.registry.is_some() {
            return Err(usage_error(
                "publish cargo takes either --lockfile PATH or -p NAME [--manifest-path PATH] [--registry NAME], not both",
            ));
        }
        return Ok((PublishRequest::CargoLockfiles(lockfiles), options));
    }
    if cargo.packages.is_empty() {
        return Err(usage_error("publish cargo requires at least one -p NAME or --lockfile PATH"));
    }
    Ok((PublishRequest::Cargo(cargo), options))
}

fn parse_npm_publish(args: &[String], index: &mut usize) -> Result<(PublishRequest, Options)> {
    let mut lockfile = None;
    let mut tarballs = Vec::new();
    let mut project = None;
    let mut options = Options::default();
    while *index < args.len() {
        let arg = args[*index].as_str();
        check_publish_option(Command::Publish, Some(Registry::Npm), arg)?;
        if take_common_option(arg, &mut options) {
            *index += 1;
            continue;
        }
        match arg {
            OPT_LOCKFILE => {
                let value = next_value(args, index, OPT_LOCKFILE)?;
                assign_once(&mut lockfile, OPT_LOCKFILE, value)?;
            }
            OPT_PROJECT => {
                let value = next_value(args, index, OPT_PROJECT)?;
                assign_once(&mut project, OPT_PROJECT, value)?;
            }
            OPT_TARBALL => {
                let value = next_value(args, index, OPT_TARBALL)?;
                tarballs.push(value.to_string());
            }
            other if other.starts_with('-') => {
                return Err(usage_error(format!("unknown option: {other}")));
            }
            other => {
                return Err(usage_error(format!(
                    "publish npm does not take positional argument '{other}'"
                )));
            }
        }
        *index += 1;
    }
    if !tarballs.is_empty() {
        if lockfile.is_some() || project.is_some() {
            return Err(usage_error(
                "publish npm takes either --tarball PATH or --lockfile PATH --project ID, not both",
            ));
        }
        return Ok((PublishRequest::NpmTarballs(tarballs), options));
    }
    let lockfile = lockfile
        .ok_or_else(|| usage_error("publish npm requires --lockfile PATH or --tarball PATH"))?;
    let project = project.ok_or_else(|| usage_error("publish npm requires --project ID"))?;
    Ok((PublishRequest::Npm(NpmPublish { lockfile, project }), options))
}

fn parse_pypi_publish(args: &[String], index: &mut usize) -> Result<(PublishRequest, Options)> {
    let mut specs = Vec::new();
    let mut wheels = Vec::new();
    let mut allow_sdist = false;
    let mut options = Options::default();
    while *index < args.len() {
        let arg = args[*index].as_str();
        check_publish_option(Command::Publish, Some(Registry::Pypi), arg)?;
        if take_common_option(arg, &mut options) {
            *index += 1;
            continue;
        }
        if arg == OPT_ALLOW_SDIST {
            allow_sdist = true;
            *index += 1;
            continue;
        }
        if arg == OPT_WHEEL {
            let value = next_value(args, index, OPT_WHEEL)?;
            if value.is_empty() {
                return Err(usage_error("--wheel requires a path"));
            }
            wheels.push(value.to_string());
            *index += 1;
            continue;
        }
        if arg.starts_with('-') {
            return Err(usage_error(format!("unknown option: {arg}")));
        }
        let spec = PypiSpec::parse(arg)
            .ok_or_else(|| usage_error(format!("invalid SPEC '{arg}': expected name==version")))?;
        specs.push(spec);
        *index += 1;
    }
    if !wheels.is_empty() {
        if !specs.is_empty() || allow_sdist {
            return Err(usage_error(
                "publish pypi takes either --wheel PATH or name==version [--allow-sdist], not both",
            ));
        }
        return Ok((PublishRequest::PypiWheels(wheels), options));
    }
    if specs.is_empty() {
        return Err(usage_error("publish pypi requires at least one name==version or --wheel PATH"));
    }
    Ok((PublishRequest::Pypi(PypiPublish { specs, allow_sdist }), options))
}

fn parse_oci_publish(args: &[String], index: &mut usize) -> Result<(OciSource, Options)> {
    let mut images = Vec::new();
    let mut layout = None;
    let mut repository = None;
    let mut tag = None;
    let mut inventory = None;
    let mut mirror_lock = None;
    let mut options = Options::default();
    while *index < args.len() {
        let arg = args[*index].as_str();
        check_publish_option(Command::Publish, Some(Registry::Oci), arg)?;
        if take_common_option(arg, &mut options) {
            *index += 1;
            continue;
        }
        match arg {
            OPT_IMAGE => {
                let value = next_value(args, index, OPT_IMAGE)?;
                let image = OciImage::parse(value).ok_or_else(|| {
                    usage_error(format!("invalid image '{value}': expected REPO=REF"))
                })?;
                images.push(image);
            }
            OPT_LAYOUT => {
                let value = next_value(args, index, OPT_LAYOUT)?;
                assign_once(&mut layout, OPT_LAYOUT, value)?;
            }
            OPT_REPOSITORY => {
                let value = next_value(args, index, OPT_REPOSITORY)?;
                assign_once(&mut repository, OPT_REPOSITORY, value)?;
            }
            OPT_TAG => {
                let value = next_value(args, index, OPT_TAG)?;
                assign_once(&mut tag, OPT_TAG, value)?;
            }
            OPT_INVENTORY => {
                let value = next_value(args, index, OPT_INVENTORY)?;
                assign_once(&mut inventory, OPT_INVENTORY, value)?;
            }
            OPT_LOCK => {
                let value = next_value(args, index, OPT_LOCK)?;
                assign_once(&mut mirror_lock, OPT_LOCK, value)?;
            }
            other if other.starts_with('-') => {
                return Err(usage_error(format!("unknown option: {other}")));
            }
            other => {
                return Err(usage_error(format!(
                    "publish oci does not take positional argument '{other}'"
                )));
            }
        }
        *index += 1;
    }
    if !images.is_empty() {
        if layout.is_some()
            || repository.is_some()
            || tag.is_some()
            || inventory.is_some()
            || mirror_lock.is_some()
        {
            return Err(usage_error(
                "publish oci accepts either --image, --layout, or --inventory/--lock, not a mix",
            ));
        }
        return Ok((OciSource::Images(images), options));
    }
    if let Some(inventory) = inventory {
        let lock = mirror_lock.ok_or_else(|| {
            usage_error("publish oci --inventory requires --lock FILE")
        })?;
        if layout.is_some() || repository.is_some() || tag.is_some() {
            return Err(usage_error(
                "publish oci accepts either --inventory/--lock or --layout, not both",
            ));
        }
        return Ok((OciSource::Mirror { inventory, lock }, options));
    }
    if mirror_lock.is_some() {
        return Err(usage_error("publish oci --lock requires --inventory FILE"));
    }
    let dir = layout.ok_or_else(|| {
        usage_error("publish oci requires --image REPO=REF, --layout DIR, or --inventory FILE --lock FILE")
    })?;
    let repository = repository
        .ok_or_else(|| usage_error("publish oci --layout requires --repository NAME"))?;
    Ok((OciSource::Layout { dir, repository, tag }, options))
}

fn parse_mirror_publish(args: &[String], index: &mut usize) -> Result<(MirrorPublish, Options)> {
    let mut manifest = None;
    let mut allow_drops = false;
    let mut options = Options::default();
    while *index < args.len() {
        let arg = args[*index].as_str();
        check_publish_option(Command::Publish, Some(Registry::Mirror), arg)?;
        if take_common_option(arg, &mut options) {
            *index += 1;
            continue;
        }
        match arg {
            OPT_MANIFEST => {
                let value = next_value(args, index, OPT_MANIFEST)?;
                if value.is_empty() {
                    return Err(usage_error("--manifest requires a path"));
                }
                assign_once(&mut manifest, OPT_MANIFEST, value)?;
            }
            OPT_ALLOW_DROPS => allow_drops = true,
            other if other.starts_with('-') => {
                return Err(usage_error(format!("unknown option: {other}")));
            }
            other => {
                return Err(usage_error(format!(
                    "publish mirror does not take positional argument '{other}'"
                )));
            }
        }
        *index += 1;
    }
    Ok((MirrorPublish { manifest, allow_drops }, options))
}

fn parse_republish(args: &[String]) -> Result<Parsed> {
    let (registry, mut index) = publish_registry(args, "republish")?;
    let mut allow_drops = false;
    let mut manifest = None;
    let mut options = Options::default();
    while index < args.len() {
        let arg = args[index].as_str();
        check_publish_option(Command::Republish, None, arg)?;
        if take_common_option(arg, &mut options) {
            index += 1;
            continue;
        }
        match arg {
            OPT_ALLOW_DROPS => allow_drops = true,
            OPT_MANIFEST => {
                if registry != Registry::Mirror {
                    return Err(usage_error("--manifest only applies to the mirror registry"));
                }
                let value = next_value(args, &mut index, OPT_MANIFEST)?;
                if value.is_empty() {
                    return Err(usage_error("--manifest requires a path"));
                }
                assign_once(&mut manifest, OPT_MANIFEST, value)?;
            }
            other if other.starts_with('-') => {
                return Err(usage_error(format!("unknown option: {other}")));
            }
            other => {
                return Err(usage_error(format!(
                    "republish does not take positional argument '{other}'"
                )));
            }
        }
        index += 1;
    }
    Ok(request_parsed(
        Command::Republish,
        Request::Republish { registry, allow_drops, options, manifest },
    ))
}

fn parse_rollback(args: &[String]) -> Result<Parsed> {
    let (registry, mut index) = publish_registry(args, "rollback")?;
    let mut generation = None;
    let mut options = Options::default();
    while index < args.len() {
        let arg = args[index].as_str();
        check_publish_option(Command::Rollback, None, arg)?;
        if take_common_option(arg, &mut options) {
            index += 1;
            continue;
        }
        match arg {
            other if other.starts_with('-') => {
                return Err(usage_error(format!("unknown option: {other}")));
            }
            other => {
                if generation.is_some() {
                    return Err(usage_error("rollback takes exactly one generation"));
                }
                generation = Some(other.to_string());
            }
        }
        index += 1;
    }
    let generation =
        generation.ok_or_else(|| usage_error("rollback requires a generation"))?;
    Ok(request_parsed(
        Command::Rollback,
        Request::Rollback { registry, generation, options },
    ))
}

pub fn help_text() -> String {
    String::from("stuff\n\nUsage: stuff <COMMAND> [OPTIONS]\n\n")
        + &reference_text()
        + OWNED_TOOL_FOOTER
}

struct HelpCommand {
    command: Command,
    registry: Option<Registry>,
    arguments: &'static str,
    description: &'static str,
    example: &'static str,
}

const HELP_COMMANDS: &[HelpCommand] = &[
    HelpCommand { command: Command::Ls, registry: None, arguments: "[OPTIONS]", description: "List registry packages.", example: "stuff ls --registry npm --versions" },
    HelpCommand { command: Command::Search, registry: None, arguments: "QUERY [OPTIONS]", description: "Search package names; QUERY is required.", example: "stuff search example --registry npm" },
    HelpCommand { command: Command::Diff, registry: None, arguments: "BEFORE AFTER [OPTIONS]", description: "Compare two required catalog paths.", example: "stuff diff before.json after.json" },
    HelpCommand { command: Command::Doctor, registry: None, arguments: "[OPTIONS]", description: "Check registry health.", example: "stuff doctor --registry npm --sample-artifacts" },
    HelpCommand { command: Command::Render, registry: None, arguments: "[OPTIONS]", description: "Render the catalog; an output path is required.", example: "stuff render --output catalog.html" },
    HelpCommand { command: Command::Publish, registry: None, arguments: "REGISTRY [OPTIONS]", description: "Publish to a registry using one of the modes below.", example: "stuff publish mirror" },
    HelpCommand { command: Command::Publish, registry: Some(Registry::Cargo), arguments: "[OPTIONS]", description: "Publish packages or mirror lockfiles; choose packages or lockfiles, not both.", example: "stuff publish cargo -p example" },
    HelpCommand { command: Command::Publish, registry: Some(Registry::Npm), arguments: "[OPTIONS]", description: "Publish lockfile packages or tarballs; lockfile requires project and excludes tarballs.", example: "stuff publish npm --lockfile pnpm-lock.yaml --project example" },
    HelpCommand { command: Command::Publish, registry: Some(Registry::Pypi), arguments: "[SPEC...] [OPTIONS]", description: "Supply at least one name==version spec or wheel; wheels exclude specs and source distributions.", example: "stuff publish pypi example==1.0" },
    HelpCommand { command: Command::Publish, registry: Some(Registry::Oci), arguments: "[OPTIONS]", description: "Supply images, a layout, or an inventory. Layout requires repository; inventory requires lock. Modes cannot be mixed.", example: "stuff publish oci --image example/app=ghcr.io/example/app:v1" },
    HelpCommand { command: Command::Publish, registry: Some(Registry::Mirror), arguments: "[OPTIONS]", description: "Mirror static upstream artifacts.", example: "stuff publish mirror --manifest mirror/manifest.toml" },
    HelpCommand { command: Command::Republish, registry: None, arguments: "REGISTRY [OPTIONS]", description: "Rebuild a registry from its published inventory.", example: "stuff republish cargo" },
    HelpCommand { command: Command::Rollback, registry: None, arguments: "REGISTRY GENERATION [OPTIONS]", description: "Activate a previous generation.", example: "stuff rollback cargo gen-1" },
    HelpCommand { command: Command::Credentials, registry: None, arguments: "BUCKET", description: "Print shell exports for a bucket's S3 gateway.", example: "stuff credentials stuff-cargo" },
    HelpCommand { command: Command::LockPath, registry: None, arguments: "BUCKET | [OPTIONS]", description: "Print the lock path for a configured bucket or registry.", example: "stuff lock-path --registry cargo" },
];

fn option_help(flag: &str) -> &'static str {
    match flag {
        OPT_REGISTRY => "NAME  Select cargo, npm, pypi, oci, or mirror (default: all for reads); Cargo publish selects its Cargo registry.",
        OPT_VERSIONS => "Include versions.", OPT_JSON => "Emit JSON.",
        OPT_SAMPLE_ARTIFACTS => "Check artifacts.", OPT_EXPECTED_GENERATION => "ID  Require a generation.",
        OPT_OUTPUT => "FILE  Required output; .txt or .md writes text, otherwise HTML.",
        OPT_CARGO_BASE | OPT_NPM_BASE | OPT_PYPI_BASE | OPT_OCI_BASE | OPT_MIRROR_BASE => "URL  Override the registry URL; corresponding STUFF_*_BASE environment variable supplies the default, otherwise the live URL.",
        OPT_CARGO_DIR | OPT_NPM_DIR | OPT_PYPI_DIR | OPT_OCI_DIR | OPT_MIRROR_DIR => "DIR  Inspect a local site, generation, or catalog.",
        OPT_DRY_RUN => "Preview without publication.", OPT_VERBOSE => "Show additional details.",
        OPT_PACKAGE => "NAME  Required unless lockfiles are supplied; repeatable.", OPT_MANIFEST_PATH => "PATH  Select a Cargo manifest.",
        OPT_LOCKFILE => "PATH  Select lockfile; repeatable for Cargo. Required unless another input mode is selected.",
        OPT_PROJECT => "ID  Select the project for the npm lockfile.", OPT_TARBALL => "PATH  Publish a tarball; repeatable.",
        OPT_ALLOW_SDIST => "Permit source distributions.", OPT_WHEEL => "PATH  Publish a wheel; repeatable.",
        OPT_IMAGE => "REPO=REF  Publish an image; repeatable.", OPT_LAYOUT => "DIR  Publish an OCI layout.", OPT_REPOSITORY => "NAME  Destination for the layout.", OPT_TAG => "TAG  Tag the layout.", OPT_INVENTORY => "FILE  Mirror an inventory.", OPT_LOCK => "FILE  Lock file for the inventory.",
        OPT_MANIFEST => "PATH  Select the mirror manifest (default mirror/manifest.toml); republish accepts this only for mirror.", OPT_ALLOW_DROPS => "Permit removals.",
        _ => unreachable!(),
    }
}

fn command_options(command: &HelpCommand) -> Vec<&'static str> {
    let mut flags = Vec::new();
    let allowed = command.command.allowed_flags();
    if allowed.registry || command.command == Command::LockPath { flags.push(OPT_REGISTRY); }
    if allowed.versions { flags.push(OPT_VERSIONS); }
    if allowed.json { flags.push(OPT_JSON); }
    if allowed.sample_artifacts { flags.push(OPT_SAMPLE_ARTIFACTS); }
    if allowed.expected_generation { flags.push(OPT_EXPECTED_GENERATION); }
    if allowed.output { flags.push(OPT_OUTPUT); }
    if allowed.base_urls { flags.extend([OPT_CARGO_BASE, OPT_NPM_BASE, OPT_PYPI_BASE, OPT_OCI_BASE, OPT_MIRROR_BASE]); }
    if allowed.local_dirs { flags.extend([OPT_CARGO_DIR, OPT_NPM_DIR, OPT_PYPI_DIR, OPT_OCI_DIR, OPT_MIRROR_DIR]); }
    match (command.command, command.registry) {
        (Command::Publish, Some(Registry::Cargo)) => flags.extend([OPT_PACKAGE, OPT_MANIFEST_PATH, OPT_REGISTRY, OPT_LOCKFILE]),
        (Command::Publish, Some(Registry::Npm)) => flags.extend([OPT_LOCKFILE, OPT_PROJECT, OPT_TARBALL]),
        (Command::Publish, Some(Registry::Pypi)) => flags.extend([OPT_ALLOW_SDIST, OPT_WHEEL]),
        (Command::Publish, Some(Registry::Oci)) => flags.extend([OPT_IMAGE, OPT_LAYOUT, OPT_REPOSITORY, OPT_TAG, OPT_INVENTORY, OPT_LOCK]),
        (Command::Publish, Some(Registry::Mirror)) => flags.extend([OPT_MANIFEST, OPT_ALLOW_DROPS]),
        (Command::Republish, _) => flags.extend([OPT_ALLOW_DROPS, OPT_MANIFEST]),
        _ => {},
    }
    if matches!(command.command, Command::Publish | Command::Republish | Command::Rollback) {
        flags.extend([OPT_DRY_RUN, OPT_JSON, OPT_VERBOSE]);
    }
    flags
}

fn reference_text() -> String {
    let mut out = String::from("Reference:\n  -h, --help  Show help offline.\n\n");
    for command in HELP_COMMANDS {
        let registry = command.registry.map(|registry| format!(" {}", registry.as_str())).unwrap_or_default();
        let _ = writeln!(out, "  stuff {}{} {}\n    {}", command.command.name(), registry, command.arguments, command.description);
        for flag in command_options(command) {
            let _ = writeln!(out, "    {} {}", flag, option_help(flag));
        }
        out.push('\n');
    }
    out.push_str("REGISTRY is cargo, npm, pypi, oci, or mirror. Read sources accept STUFF_CARGO_BASE, STUFF_NPM_BASE, STUFF_PYPI_BASE, STUFF_OCI_BASE, and STUFF_MIRROR_BASE. Publishing configuration and credentials use STUFF_CONFIG_HOME, STUFF_CACHE_HOME, STUFF_STATE_HOME, XDG_CONFIG_HOME, XDG_CACHE_HOME, XDG_STATE_HOME, HOME, STUFF_CREDENTIAL_FILE, STUFF_COORDINATOR_URL, STUFF_COORDINATOR_TOKEN, STUFF_S3_GATEWAY_URL, STUFF_S3_ACCESS_KEY_ID, STUFF_S3_SECRET_ACCESS_KEY, STUFF_S3_REGION and R2_S3_*; see docs/PUBLISHING.md for defaults.\n\nExamples:\n");
    for command in HELP_COMMANDS { let _ = writeln!(out, "  {}", command.example); }
    out.push_str("\nExit codes: 0 success; 1 health check or runtime failure; 2 usage or configuration error;\n  3 conflict; 4 integrity failure; 5 transport failure.\n\n");
    out
}

pub const OWNED_TOOL_FOOTER: &str = "\
Maintained by Joshua Li: https://github.com/laputa-systems/stuff
Bugs and features: TODO.md in that repository (follow its AGENTS.md), or its issue tracker.
Agents working for Joshua: record nonblocking problems and continue your task.
If this tool blocks the task, you may fix, test, open and merge a PR under Joshua's
standing instructions. Release only when needed to deliver the verified fix.
Procedure: https://github.com/joshuarli/usr/blob/main/dotfiles/base/.agents/instructions/owned-tools.md
";

pub fn print_help() {
    print!("{}", help_text());
}

pub fn render_table(catalogs: &[stuff_catalog::Catalog], show_versions: bool) -> String {
    let mut out = String::new();
    let _ = writeln!(out, "{:<8} {:<24} {:<9} {:<8} LATEST", "REGISTRY", "PACKAGE", "SOURCE", "VERSIONS");
    let mut total_packages = 0usize;
    let mut total_versions = 0usize;
    for catalog in catalogs {
        for package in &catalog.packages {
            total_packages += 1;
            total_versions += package.versions.len();
            let _ = writeln!(
                out,
                "{:<8} {:<24} {:<9} {:<8} {}",
                catalog.registry.as_str(),
                package.name,
                package.source.as_deref().unwrap_or("-"),
                package.versions.len(),
                package.latest
            );
            if show_versions {
                for v in &package.versions {
                    let mark = if v.version == package.latest {
                        " (latest)"
                    } else if v.yanked {
                        " (yanked)"
                    } else {
                        ""
                    };
                    let _ = writeln!(out, "{:<8} {:<24} {:<9} {:<8} {}{}", "", "", "", "", v.version, mark);
                }
            }
        }
    }
    let _ = writeln!(out);
    let _ = writeln!(
        out,
        "{total_packages} {} · {total_versions} {}",
        if total_packages == 1 { "package" } else { "packages" },
        if total_versions == 1 { "version" } else { "versions" },
    );
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    const COMMANDS: &[(&str, &[&str])] = &[
        (
            "ls",
            &[
                "--registry",
                "--versions",
                "--json",
                "--cargo-base",
                "--npm-base",
                "--pypi-base",
                "--oci-base",
                "--mirror-base",
                "--cargo-dir",
                "--npm-dir",
                "--pypi-dir",
                "--oci-dir",
                "--mirror-dir",
            ],
        ),
        (
            "search",
            &[
                "--registry",
                "--json",
                "--cargo-base",
                "--npm-base",
                "--pypi-base",
                "--oci-base",
                "--mirror-base",
                "--cargo-dir",
                "--npm-dir",
                "--pypi-dir",
                "--oci-dir",
                "--mirror-dir",
            ],
        ),
        ("diff", &["--json"]),
        (
            "doctor",
            &[
                "--registry",
                "--expected-generation",
                "--sample-artifacts",
                "--cargo-base",
                "--npm-base",
                "--pypi-base",
                "--oci-base",
                "--mirror-base",
                "--cargo-dir",
                "--npm-dir",
                "--pypi-dir",
                "--oci-dir",
                "--mirror-dir",
            ],
        ),
        (
            "render",
            &[
                "--output",
                "--registry",
                "--cargo-base",
                "--npm-base",
                "--pypi-base",
                "--oci-base",
                "--mirror-base",
                "--cargo-dir",
                "--npm-dir",
                "--pypi-dir",
                "--oci-dir",
                "--mirror-dir",
            ],
        ),
    ];

    const ALL_FLAGS: &[&str] = &[
        "--registry",
        "--versions",
        "--json",
        "--sample-artifacts",
        "--cargo-base",
        "--npm-base",
        "--pypi-base",
        "--oci-base",
        "--mirror-base",
        "--cargo-dir",
        "--npm-dir",
        "--pypi-dir",
        "--oci-dir",
        "--mirror-dir",
        "--output",
        "--expected-generation",
        "--remote",
    ];

    fn args(v: &[&str]) -> Vec<String> {
        v.iter().map(|s| s.to_string()).collect()
    }

    fn base_args(command: &str) -> Vec<&'static str> {
        match command {
            "ls" => vec!["ls"],
            "search" => vec!["search", "query"],
            "diff" => vec!["diff", "before.json", "after.json"],
            "doctor" => vec!["doctor"],
            "render" => vec!["render"],
            _ => unreachable!(),
        }
    }

    fn flag_value(flag: &str) -> Option<&'static str> {
        match flag {
            "--registry" => Some("npm"),
            "--cargo-base" | "--npm-base" | "--pypi-base" | "--oci-base" | "--mirror-base" => Some("https://example.com"),
            "--cargo-dir" | "--npm-dir" | "--pypi-dir" | "--oci-dir" | "--mirror-dir" => Some("."),
            "--output" => Some("out.html"),
            "--expected-generation" => Some("gen1"),
            _ => None,
        }
    }

    fn supports(command: &str, flag: &str) -> bool {
        COMMANDS
            .iter()
            .find(|(name, _)| *name == command)
            .is_some_and(|(_, flags)| flags.contains(&flag))
    }

    #[test]
    fn parses_ls_variants() {
        let p = parse_args(&args(&["ls"])).unwrap();
        assert_eq!(p.command, Command::Ls);
        let p = parse_args(&args(&["ls", "--registry", "npm", "--versions", "--json"])).unwrap();
        assert_eq!(p.registry, Some(RegistryFilter::Npm));
        assert!(p.versions && p.json);
        assert_eq!(
            parse_args(&args(&["ls", "--registry", "oci"])).unwrap().registry,
            Some(RegistryFilter::Oci)
        );
        assert!(parse_args(&args(&["ls", "--registry", "bogus"])).is_err());
        assert!(parse_args(&args(&["ls", "extra"])).is_err());
    }

    #[test]
    fn every_command_rejects_each_unsupported_flag() {
        for (command, _) in COMMANDS {
            for flag in ALL_FLAGS.iter().copied() {
                let mut argv = base_args(command);
                argv.push(flag);
                if let Some(value) = flag_value(flag) {
                    argv.push(value);
                }
                let result = parse_args(&args(&argv));
                if supports(command, flag) {
                    assert!(result.is_ok(), "{command} rejected supported {flag}: {:?}", result.err());
                } else {
                    let err = result.expect_err(&format!("{command} accepted unsupported {flag}"));
                    assert!(matches!(err, Error::Usage(_)), "{command} {flag}: {err}");
                    assert_eq!(err.exit_code(), 2);
                }
            }
        }
    }

    #[test]
    fn help_advertises_only_accepted_flags_and_positionals() {
        let help = help_text();
        assert!(!help.contains("[sources...]"), "{help}");
        assert!(!help.contains("--remote"), "{help}");
        let reference = help.split_once("Examples:\n").unwrap().0;
        for (command, _) in COMMANDS {
            let prefix = format!("  stuff {command} ");
            let block = reference.split_once(&prefix).unwrap().1.split_once("\n\n").unwrap().0;
            let advertised: Vec<String> = block.lines().filter_map(|line| {
                let text = line.strip_prefix("    --")?;
                Some(format!("--{}", text.split_whitespace().next().unwrap()))
            }).collect();
            check_advertised(command, &advertised);
        }
    }

    #[test]
    fn publishing_help_options_match_parser() {
        let help = help_text();
        let reference = help.split_once("Examples:\n").unwrap().0;
        let cases: &[(&str, &[&str])] = &[
            ("publish cargo", &["publish", "cargo", "-p", "example"]),
            ("publish npm", &["publish", "npm", "--tarball", "example.tgz"]),
            ("publish pypi", &["publish", "pypi", "example==1.0"]),
            ("publish oci", &["publish", "oci", "--image", "example=example:v1"]),
            ("publish mirror", &["publish", "mirror"]),
            ("republish", &["republish", "mirror"]),
            ("rollback", &["rollback", "cargo", "gen-1"]),
        ];
        let flags = ["-p", "--manifest-path", "--registry", "--lockfile", "--project", "--tarball", "--allow-sdist", "--wheel", "--image", "--layout", "--repository", "--tag", "--inventory", "--lock", "--manifest", "--allow-drops", "--dry-run", "--json", "--verbose", "--output"];
        for (command, base) in cases {
            let prefix = format!("  stuff {command} ");
            let block = reference.split_once(&prefix).unwrap().1.split_once("\n\n").unwrap().0;
            let advertised: Vec<&str> = block.lines().filter_map(|line| {
                let line = line.strip_prefix("    -")?;
                Some(line.split_whitespace().next().unwrap())
            }).collect();
            for flag in flags {
                let mut argv = base.to_vec();
                argv.push(flag);
                if !matches!(flag, "--allow-sdist" | "--allow-drops" | "--dry-run" | "--json" | "--verbose") {
                    argv.push("example");
                }
                let parsed = parse_args(&args(&argv));
                let recognized = match parsed {
                    Ok(_) => true,
                    Err(error) => !error.to_string().contains("unknown option:"),
                };
                assert_eq!(advertised.contains(&&flag[1..]), recognized, "{command} {flag}: {argv:?}");
            }
        }
    }

    fn publish_request(argv: &[&str]) -> (PublishRequest, Options) {
        match parse_args(&args(argv)).unwrap().request.unwrap() {
            Request::Publish { request, options } => (request, options),
            other => panic!("{other:?}"),
        }
    }

    fn usage_rejected(argv: &[&str]) {
        let error = parse_args(&args(argv)).unwrap_err();
        assert!(matches!(error, Error::Usage(_)), "{argv:?}: {error}");
        assert_eq!(error.exit_code(), 2, "{argv:?}");
    }

    #[test]
    fn parses_publish_cargo_grammar() {
        let (request, options) = publish_request(&[
            "publish",
            "cargo",
            "-p",
            "alpha",
            "-p",
            "beta",
            "--manifest-path",
            "Cargo.toml",
            "--registry",
            "local",
            "--dry-run",
            "--json",
            "--verbose",
        ]);
        let PublishRequest::Cargo(cargo) = request else { panic!("{request:?}") };
        assert_eq!(cargo.packages, vec!["alpha", "beta"]);
        assert_eq!(cargo.manifest_path.as_deref(), Some("Cargo.toml"));
        assert_eq!(cargo.registry.as_deref(), Some("local"));
        assert!(options.dry_run && options.json && options.verbose);
    }

    #[test]
    fn parses_publish_npm_grammar() {
        let (request, options) =
            publish_request(&["publish", "npm", "--lockfile", "pnpm-lock.yaml", "--project", "site", "--json"]);
        let PublishRequest::Npm(npm) = request else { panic!("{request:?}") };
        assert_eq!(npm.lockfile, "pnpm-lock.yaml");
        assert_eq!(npm.project, "site");
        assert!(options.json && !options.dry_run);
    }

    #[test]
    fn parses_publish_npm_tarballs() {
        let (request, options) =
            publish_request(&["publish", "npm", "--tarball", "a.tgz", "--tarball", "b.tgz", "--dry-run"]);
        let PublishRequest::NpmTarballs(tarballs) = request else { panic!("{request:?}") };
        assert_eq!(tarballs, vec!["a.tgz", "b.tgz"]);
        assert!(options.dry_run);
    }

    #[test]
    fn parses_publish_pypi_grammar() {
        let (request, options) =
            publish_request(&["publish", "pypi", "alpha==1.0.0", "beta==2.0.0", "--allow-sdist", "--dry-run"]);
        let PublishRequest::Pypi(pypi) = request else { panic!("{request:?}") };
        assert_eq!(pypi.specs.len(), 2);
        assert_eq!(pypi.specs[0].name, "alpha");
        assert_eq!(pypi.specs[0].version, "1.0.0");
        assert_eq!(pypi.specs[1].name, "beta");
        assert!(pypi.allow_sdist);
        assert!(options.dry_run);
    }

    #[test]
    fn parses_publish_pypi_wheels() {
        let (request, options) =
            publish_request(&["publish", "pypi", "--wheel", "a.whl", "--wheel", "b.whl", "--json"]);
        let PublishRequest::PypiWheels(wheels) = request else { panic!("{request:?}") };
        assert_eq!(wheels, vec!["a.whl", "b.whl"]);
        assert!(options.json);
    }

    #[test]
    fn parses_publish_mirror_grammar() {
        let (request, options) = publish_request(&["publish", "mirror"]);
        let PublishRequest::Mirror(mirror) = request else { panic!("{request:?}") };
        assert_eq!(mirror.manifest, None);
        assert!(!mirror.allow_drops);
        assert!(!options.dry_run);

        let (request, options) = publish_request(&[
            "publish",
            "mirror",
            "--manifest",
            "custom.toml",
            "--allow-drops",
            "--dry-run",
            "--json",
            "--verbose",
        ]);
        let PublishRequest::Mirror(mirror) = request else { panic!("{request:?}") };
        assert_eq!(mirror.manifest.as_deref(), Some("custom.toml"));
        assert!(mirror.allow_drops);
        assert!(options.dry_run && options.json && options.verbose);
    }

    #[test]
    fn republish_accepts_manifest_only_for_the_mirror() {
        match parse_args(&args(&["republish", "mirror", "--manifest", "custom.toml", "--allow-drops"]))
            .unwrap()
            .request
            .unwrap()
        {
            Request::Republish { registry, allow_drops, manifest, .. } => {
                assert_eq!(registry, Registry::Mirror);
                assert_eq!(manifest.as_deref(), Some("custom.toml"));
                assert!(allow_drops);
            }
            other => panic!("{other:?}"),
        }
        for argv in [
            vec!["republish", "cargo", "--manifest", "custom.toml"],
            vec!["republish", "npm", "--manifest", "custom.toml"],
            vec!["republish", "mirror", "--manifest"],
        ] {
            usage_rejected(&argv);
        }
    }

    #[test]
    fn parses_both_publish_oci_forms() {
        let (request, _) =
            publish_request(&["publish", "oci", "--image", "repo/a=1.0", "--image", "repo/b=2.0"]);
        let PublishRequest::Oci(OciSource::Images(images)) = request else { panic!("{request:?}") };
        assert_eq!(images.len(), 2);
        assert_eq!(images[0].repository, "repo/a");
        assert_eq!(images[0].reference, "1.0");

        let (request, options) = publish_request(&[
            "publish",
            "oci",
            "--layout",
            "dir",
            "--repository",
            "repo/name",
            "--tag",
            "latest",
            "--dry-run",
        ]);
        let PublishRequest::Oci(OciSource::Layout { dir, repository, tag }) = request else {
            panic!("{request:?}")
        };
        assert_eq!(dir, "dir");
        assert_eq!(repository, "repo/name");
        assert_eq!(tag.as_deref(), Some("latest"));
        assert!(options.dry_run);

        let (request, options) = publish_request(&[
            "publish",
            "oci",
            "--inventory",
            "mirror.toml",
            "--lock",
            "mirror.lock",
            "--json",
        ]);
        let PublishRequest::Oci(OciSource::Mirror { inventory, lock }) = request else {
            panic!("{request:?}")
        };
        assert_eq!(inventory, "mirror.toml");
        assert_eq!(lock, "mirror.lock");
        assert!(options.json);
    }

    #[test]
    fn publish_rejects_bad_grammar_with_exit_two() {
        for argv in [
            vec!["publish"],
            vec!["publish", "bogus"],
            vec!["publish", "cargo"],
            vec!["publish", "cargo", "-p"],
            vec!["publish", "cargo", "-p", "x", "--allow-drops"],
            vec!["publish", "cargo", "-p", "x", "extra"],
            vec!["publish", "npm"],
            vec!["publish", "npm", "--lockfile", "l"],
            vec!["publish", "npm", "--project", "p"],
            vec!["publish", "npm", "--lockfile", "l", "--project", "p", "--tag", "t"],
            vec!["publish", "npm", "--tarball"],
            vec!["publish", "npm", "--tarball", "a.tgz", "--lockfile", "l"],
            vec!["publish", "npm", "--tarball", "a.tgz", "--project", "p"],
            vec!["publish", "pypi"],
            vec!["publish", "pypi", "not-a-spec"],
            vec!["publish", "pypi", "name=="],
            vec!["publish", "pypi", "==1.0"],
            vec!["publish", "pypi", "--wheel"],
            vec!["publish", "pypi", "--wheel", "a.whl", "alpha==1.0"],
            vec!["publish", "pypi", "--wheel", "a.whl", "--allow-sdist"],
            vec!["publish", "oci"],
            vec!["publish", "oci", "--layout", "dir"],
            vec!["publish", "oci", "--repository", "repo"],
            vec!["publish", "oci", "--tag", "latest"],
            vec!["publish", "oci", "--image", "bad"],
            vec!["publish", "oci", "--image", "repo="],
            vec!["publish", "oci", "--image", "=ref"],
            vec!["publish", "oci", "--image", "repo=ref", "--layout", "dir"],
            vec!["publish", "oci", "--image", "repo=ref", "--inventory", "mirror.toml"],
            vec!["publish", "oci", "--image", "repo=ref", "--repository", "repo"],
            vec!["publish", "oci", "--image", "repo=ref", "--tag", "latest"],
            vec!["publish", "oci", "--layout", "dir", "--repository", "repo", "extra"],
            vec!["publish", "oci", "--inventory", "mirror.toml"],
            vec!["publish", "oci", "--lock", "mirror.lock"],
            vec!["publish", "oci", "--inventory", "mirror.toml", "--layout", "dir"],
            vec!["publish", "oci", "--inventory", "mirror.toml", "--lock", "mirror.lock", "--repository", "repo"],
            vec!["publish", "oci", "--inventory", "mirror.toml", "--lock", "mirror.lock", "--tag", "t"],
            vec!["publish", "oci", "--inventory", "mirror.toml", "--lock", "mirror.lock", "--image", "repo=ref"],
            vec!["publish", "mirror", "extra"],
            vec!["publish", "mirror", "--bogus"],
            vec!["publish", "mirror", "--manifest"],
            vec!["publish", "mirror", "--registry", "cargo"],
        ] {
            usage_rejected(&argv);
        }
    }

    #[test]
    fn parses_republish_and_rollback_grammar() {
        match parse_args(&args(&["republish", "cargo", "--allow-drops", "--dry-run", "--json"]))
            .unwrap()
            .request
            .unwrap()
        {
            Request::Republish { registry, allow_drops, options, manifest } => {
                assert_eq!(registry, Registry::Cargo);
                assert_eq!(manifest, None);
                assert!(allow_drops && options.dry_run && options.json && !options.verbose);
            }
            other => panic!("{other:?}"),
        }
        match parse_args(&args(&["rollback", "oci", "gen-42", "--json", "--verbose"]))
            .unwrap()
            .request
            .unwrap()
        {
            Request::Rollback { registry, generation, options } => {
                assert_eq!(registry, Registry::Oci);
                assert_eq!(generation, "gen-42");
                assert!(options.json && options.verbose && !options.dry_run);
            }
            other => panic!("{other:?}"),
        }
    }

    #[test]
    fn republish_and_rollback_reject_bad_grammar_with_exit_two() {
        for argv in [
            vec!["republish"],
            vec!["republish", "bogus"],
            vec!["republish", "cargo", "extra"],
            vec!["republish", "cargo", "--image", "repo=ref"],
            vec!["republish", "mirror", "--image", "repo=ref"],
            vec!["rollback"],
            vec!["rollback", "bogus", "gen"],
            vec!["rollback", "cargo"],
            vec!["rollback", "cargo", "gen-1", "gen-2"],
            vec!["rollback", "cargo", "gen", "--allow-drops"],
        ] {
            usage_rejected(&argv);
        }
    }

    fn check_advertised(command: &str, advertised: &[String]) {
        for flag in advertised {
            assert!(supports(command, flag), "{command} help advertises unsupported {flag}");
            let mut argv = base_args(command);
            argv.push(flag);
            if let Some(value) = flag_value(flag) {
                argv.push(value);
            }
            assert!(parse_args(&args(&argv)).is_ok(), "{command} help advertises rejected {flag}");
        }
        let (_, supported) = COMMANDS.iter().find(|(name, _)| *name == command).unwrap();
        for flag in supported.iter() {
            assert!(
                advertised.iter().any(|advertised| advertised == flag),
                "{command} help does not advertise {flag}"
            );
        }
    }

}

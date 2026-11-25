from __future__ import annotations

from repomod import owned_dockerfile

IMAGE = "oci.example/owned-tools@sha256:" + "a" * 64
PACKAGES = (
    "git", "cmake", "ripgrep", "fd", "jaq", "meson", "ninja", "ninja-build",
    "samurai", "clang", "lld", "llvm", "^clang-?\\d+$", "^lld-?\\d+$",
    "^llvm-?\\d+$", "mold", "ffmpeg",
)


def rewrite(text: str, keep=lambda name: False) -> owned_dockerfile.Rewrite:
    return owned_dockerfile.rewrite(text, PACKAGES, IMAGE, keep)


def test_removes_pinned_packages_and_inserts_image_lines() -> None:
    out = rewrite(
        "FROM alpine:3.20 AS build\n"
        "RUN apk add --no-cache \\\n"
        "    git=2.45.2-r0 cmake=3.28.3-r0 curl\n"
    )
    assert out.text == (
        "FROM alpine:3.20 AS build\n"
        f"COPY --from={IMAGE} /opt/laputa /opt/laputa\n"
        "ENV PATH=$PATH:/opt/laputa/bin\n"
        "RUN apk add --no-cache \\\n"
        "    curl\n"
    )
    assert out.removed == frozenset({(2, "cmake"), (2, "git")})


def test_drops_run_that_becomes_empty() -> None:
    out = rewrite(
        "FROM alpine\n"
        "RUN apk add --no-cache meson ninja-build samurai\n"
        "RUN apk add curl\n"
    )
    assert out.text == (
        "FROM alpine\n"
        f"COPY --from={IMAGE} /opt/laputa /opt/laputa\n"
        "ENV PATH=$PATH:/opt/laputa/bin\n"
        "RUN apk add curl\n"
    )
    assert out.removed == frozenset({(2, "meson"), (2, "ninja-build"), (2, "samurai")})


def test_drops_emptied_and_chain_command() -> None:
    out = rewrite("FROM alpine\nRUN make deps && apk add mold\n")
    assert "RUN make deps\n" in out.text
    assert "apk add" not in out.text
    assert out.removed == frozenset({(2, "mold")})


def test_drops_leading_and_chain_command() -> None:
    out = rewrite("FROM alpine\nRUN apk add git && make deps\n")
    assert "RUN make deps\n" in out.text
    assert out.removed == frozenset({(2, "git")})


def test_versioned_llvm_packages_match_patterns() -> None:
    out = rewrite("FROM alpine\nRUN apk add clang19=19.1.4-r0 lld-20 llvm21 curl\n")
    assert "RUN apk add curl\n" in out.text
    assert out.removed == frozenset({(2, "clang19"), (2, "lld-20"), (2, "llvm21")})


def test_existing_copy_digest_is_updated() -> None:
    old = "oci.example/owned-tools@sha256:" + "0" * 64
    out = rewrite(
        "FROM alpine AS runtime\n"
        f"COPY --from={old} /opt/laputa /opt/laputa\n"
        "ENV PATH=$PATH:/opt/laputa/bin\n"
        "RUN apk add --no-cache git fd\n"
    )
    assert out.text == (
        "FROM alpine AS runtime\n"
        f"COPY --from={IMAGE} /opt/laputa /opt/laputa\n"
        "ENV PATH=$PATH:/opt/laputa/bin\n"
    )
    assert out.text.count("COPY --from") == 1


def test_existing_env_path_is_not_duplicated() -> None:
    out = rewrite(
        "FROM alpine\n"
        "COPY --from=other/image /opt/laputa /opt/laputa\n"
        "ENV PATH=$PATH:/opt/laputa/bin OTHER=1\n"
        "RUN apk add git\n"
    )
    assert out.text.count("ENV PATH=") == 1
    assert out.text.count("COPY --from") == 2


def test_apt_stage_is_untouched() -> None:
    text = "FROM debian:bookworm\nRUN apt-get install -y git cmake\n"
    out = rewrite(text)
    assert out.text == text
    assert out.removed == frozenset()


def test_non_alpine_apk_stage_is_untouched() -> None:
    text = "FROM busybox\nRUN apk add git\n"
    out = rewrite(text)
    assert out.text == text


def test_unmapped_packages_keep_the_stage_clean() -> None:
    text = "FROM alpine\nRUN apk add --no-cache python3=3.12.0-r0 py3-pip curl\n"
    out = rewrite(text)
    assert out.text == text
    assert out.removed == frozenset()


def test_unsafe_run_constructs_are_left_alone() -> None:
    for command in (
        "if apk add git; then make; fi",
        "apk add git | tee log",
        "apk add git &",
        "sh -c 'apk add git'",
        "apk add $(cat list)",
        "apk add git # comment",
        "apk add --unknown-flag git",
    ):
        text = f"FROM alpine\nRUN {command}\n"
        out = rewrite(text)
        assert out.text == text, command
        assert out.removed == frozenset(), command


def test_keep_callback_preserves_exempt_packages() -> None:
    out = rewrite(
        "FROM alpine\nRUN apk add git cmake curl\n",
        keep=lambda name: name == "git",
    )
    assert "RUN apk add git curl\n" in out.text
    assert out.removed == frozenset({(2, "cmake")})


def test_multi_stage_gets_one_copy_per_touched_stage() -> None:
    out = rewrite(
        "FROM alpine AS a\nRUN apk add git\n"
        "FROM alpine AS b\nRUN apk add curl\n"
        "FROM alpine AS c\nRUN apk add cmake\n"
    )
    assert out.text.count("COPY --from=") == 2
    assert out.text.count("ENV PATH=") == 2


def test_keeps_continuation_layout_and_drops_emptied_lines() -> None:
    out = rewrite(
        "FROM alpine:3.20\n"
        "RUN apk add --no-cache \\\n"
        "        bash build-base git mold \\\n"
        "        cmake=3.28.3-r0 \\\n"
        "    && git config --global x y \\\n"
        "    && make\n"
    )
    assert out.text == (
        "FROM alpine:3.20\n"
        f"COPY --from={IMAGE} /opt/laputa /opt/laputa\n"
        "ENV PATH=$PATH:/opt/laputa/bin\n"
        "RUN apk add --no-cache \\\n"
        "        bash build-base \\\n"
        "    && git config --global x y \\\n"
        "    && make\n"
    )
    assert out.removed == frozenset({(2, "git"), (2, "mold"), (2, "cmake")})


def test_emptied_last_line_closes_the_continuation() -> None:
    out = rewrite(
        "FROM alpine:3.20\n"
        "RUN apk add --no-cache curl \\\n"
        "    git\n"
    )
    assert out.text == (
        "FROM alpine:3.20\n"
        f"COPY --from={IMAGE} /opt/laputa /opt/laputa\n"
        "ENV PATH=$PATH:/opt/laputa/bin\n"
        "RUN apk add --no-cache curl\n"
    )


def test_prepended_path_is_rewritten_to_append() -> None:
    out = rewrite(
        "FROM alpine:3.20\n"
        f"COPY --from={IMAGE} /opt/laputa /opt/laputa\n"
        "ENV PATH=/opt/laputa/bin:$PATH\n"
        "RUN apk add --no-cache python3\n"
    )
    assert out.text == (
        "FROM alpine:3.20\n"
        f"COPY --from={IMAGE} /opt/laputa /opt/laputa\n"
        "ENV PATH=$PATH:/opt/laputa/bin\n"
        "RUN apk add --no-cache python3\n"
    )
    assert out.removed == frozenset()
    assert out.prepended == frozenset({3})

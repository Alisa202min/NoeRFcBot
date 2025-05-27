{ pkgs }:
pkgs.mkShell {
  buildInputs = [
    pkgs.postgresql_16  # PostgreSQL version 16
  ];
}
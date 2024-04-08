{
  description = "nec-opt";

  inputs = {
      nixpkgs.url = "nixpkgs/nixos-unstable";
      flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { nixpkgs, flake-utils, ... }:
    let
      system = flake-utils.lib.system.x86_64-linux;
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true;
    };
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages = [
          (pkgs.python3.withPackages (p: [
            p.numpy
            p.pyomo
          ]))
          pkgs.cbc
          pkgs.glpk
          pkgs.ipopt
        ];
      };
    };
}
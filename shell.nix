{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
    packages = with pkgs; [
        python312Full
        virtualenv
        python312Packages.pip
        nodePackages.pyright
        # ruff-lsp
    ];

    # shellHook = ''
    # '';
}

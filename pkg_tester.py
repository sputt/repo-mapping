from python.runfiles import Runfiles

RUNFILES = Runfiles.Create()

def main() -> None:
    with open(RUNFILES.Rlocation("_repo_mapping"), "r") as fh:
        full_manifest = fh.readlines()
    
    print(len(full_manifest))

if __name__ == "__main__":
    main()

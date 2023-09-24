from executors.refreshExecutor import RefreshExecutor
from executors.payoutsExecutor import PayoutsExecutor

def main():

    # executors
    refresher = RefreshExecutor()
    payouter = PayoutsExecutor()

    # refresh sports
    refresher.refreshSports()

    # receive funds
    payouter.receiveFunds()

    # send payouts
    payouter.sendPayouts()

    return({"ok": True})

if __name__ == "__main__":
    main()

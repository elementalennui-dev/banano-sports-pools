from executors.refreshExecutor import RefreshExecutor
from executors.payoutsExecutor import PayoutsExecutor

import warnings
warnings.filterwarnings('ignore')

def main():

    # executors
    refresher = RefreshExecutor()
    payouter = PayoutsExecutor()

    # refresh sports
    try:
        refresher.refreshSports()
    except Exception as e:
        print("Refreshing sports failed. More info below:")
        print(e)

    # receive funds
    payouter.receiveFunds()

    # send payouts
    payouter.sendPayouts()

    return({"ok": True})

if __name__ == "__main__":
    main()

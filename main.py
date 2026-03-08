import machine, sys
import listener_app

cause_constants = ["ZERO", "PWRON_RESET", "HARD_RESET", "WDT_RESET", "DEEPSLEEP_RESET", "SOFT_RESET", "BROWN_OUT_RESET"]
reset_cause = machine.reset_cause()
print("reset_cause={}: {}".format(reset_cause, cause_constants[reset_cause] if reset_cause < len(cause_constants) else "unknown"), end='')
if reset_cause != machine.DEEPSLEEP_RESET:
    print('; clearing RTC memory')
    machine.RTC().memory(b'')
else:
    print('')

if 1:
    try:
        listener_app.main()
    except Exception as e:
        print("Fatal error in main:")
        sys.print_exception(e)

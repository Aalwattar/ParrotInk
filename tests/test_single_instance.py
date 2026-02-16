from engine.platform_win.instance import SingleInstance


def test_single_instance_detection():
    # 1. Create first instance
    mutex_name = r"Local\Test_ParrotInk_Mutex_Unique"
    instance1 = SingleInstance(mutex_name)
    assert instance1.already_running is False
    assert instance1.mutex_handle is not None

    # 2. Try to create second instance with same name
    instance2 = SingleInstance(mutex_name)
    assert instance2.already_running is True

    # Clean up instance2 (instance1 still holds the mutex)
    del instance2

    # 3. Clean up instance1 and verify a new one can be created
    del instance1

    instance3 = SingleInstance(mutex_name)
    assert instance3.already_running is False
    del instance3

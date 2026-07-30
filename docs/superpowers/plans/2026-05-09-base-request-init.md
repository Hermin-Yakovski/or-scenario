# BaseRequest in Scenario.__init__ Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update `Scenario.__init__` to accept an optional `BaseRequest` parameter, ensuring `_request` is always set to a valid instance.

**Architecture:** The base `Scenario` class now manages request initialization. If no request is provided, a default `BaseRequest()` with auto-generated `request_id` is created. This eliminates boilerplate in subclasses while maintaining backward compatibility through the optional parameter.

**Tech Stack:** Python 3.11+, Pydantic 2.0+, pytest

---

## Task 1: Update Scenario.__init__ Signature

**Files:**
- Modify: `or_scenario/scenario.py:37-41`

- [ ] **Step 1: Write the failing test**

First, write a test that verifies the new behavior - creating a Scenario without a request should work and _request should be set:

```python
def test_scenario_init_with_default_request():
    """Test Scenario can be initialized without request, creates default."""
    scenario = Scenario()
    assert scenario._request is not None
    assert isinstance(scenario._request, BaseRequest)
    assert scenario._version_id == scenario._request.request_id
```

Add this test to `tests/test_scenario.py` after line 38 (after `test_scenario_init`).

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scenario.py::test_scenario_init_with_default_request -v`

Expected: FAIL - The current `__init__` requires a `version_id` positional argument, and `_request` is set to `None`.

- [ ] **Step 3: Write minimal implementation**

Update `or_scenario/scenario.py` line 37-41. Replace:

```python
def __init__(self, version_id: Hashable) -> None:
    self._version_id = version_id
    self._algorithm = None
    self._data = Register[Parameter]()
    self._request = None
```

With:

```python
def __init__(self, request: Optional[BaseRequest] = None) -> None:
    """Initialize scenario with a base request.

    Args:
        request: Optional BaseRequest containing scenario configuration.
                If None, a default BaseRequest with auto-generated request_id is created.
    """
    if request is None:
        self._request = BaseRequest()
    self._version_id = self._request.request_id
    self._algorithm = None
    self._data = Register[Parameter]()
```

Also update line 35 to change the type annotation:

```python
_request: BaseRequest
```

(Previously was `_request: Optional[BaseRequest]`)

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_scenario_init_with_default_request -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_scenario/scenario.py tests/test_scenario.py
git commit -m "feat: Scenario.__init__ accepts optional BaseRequest, defaults to BaseRequest()"
```

---

## Task 2: Add Test for Explicit Request Passing

**Files:**
- Modify: `tests/test_scenario.py`

- [ ] **Step 1: Write the test**

Add this test after `test_scenario_init_with_default_request`:

```python
def test_scenario_init_with_explicit_request():
    """Test Scenario can be initialized with explicit BaseRequest."""
    request = BaseRequest()
    scenario = Scenario(request)
    assert scenario._request is request
    assert scenario._version_id == request.request_id
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_scenario_init_with_explicit_request -v`

Expected: PASS (implementation from Task 1 already handles this)

- [ ] **Step 3: Commit**

```bash
git add tests/test_scenario.py
git commit -m "test: add test for explicit BaseRequest passing"
```

---

## Task 3: Update test_scenario_init (Existing Test)

**Files:**
- Modify: `tests/test_scenario.py:31-38`

- [ ] **Step 1: Update the test**

The existing `test_scenario_init` test calls `Scenario(1)` which will now fail because `__init__` expects a BaseRequest or nothing. Replace lines 31-38:

```python
def test_scenario_init():
    """Test Scenario can be initialized with version_id."""
    scenario = Scenario(1)
    assert scenario._version_id == 1
    assert scenario._algorithm is None
    assert isinstance(scenario._data, Register)
    # After refactor, _load_step is a static decorator method, not an instance attribute
    assert callable(Scenario._load_step)
```

With:

```python
def test_scenario_init():
    """Test Scenario can be initialized without arguments."""
    scenario = Scenario()
    assert scenario._version_id == scenario._request.request_id
    assert scenario._algorithm is None
    assert isinstance(scenario._data, Register)
    assert isinstance(scenario._request, BaseRequest)
    # After refactor, _load_step is a static decorator method, not an instance attribute
    assert callable(Scenario._load_step)
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_scenario_init -v`

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_scenario.py
git commit -m "test: update test_scenario_init for new signature"
```

---

## Task 4: Update Subclass __init__ Calls in Tests

**Files:**
- Modify: `tests/test_scenario.py`

Many test scenarios define `__init__` methods that call `super().__init__(version_id)`. These need to be updated.

- [ ] **Step 1: Update DecoratorTestScenario in test_decorator_transforms**

Lines 48-52 define a test scenario. Update:

```python
class DecoratorTestScenario(Scenario):
    def __init__(self, version_id):
        super().__init__(version_id)
        self.mapping_called = False
        self.received_records = None
```

To:

```python
class DecoratorTestScenario(Scenario):
    def __init__(self):
        super().__init__()
        self.mapping_called = False
        self.received_records = None
```

And update line 60 from:

```python
scenario = DecoratorTestScenario(1)
```

To:

```python
scenario = DecoratorTestScenario()
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_decorator_transforms_method -v`

Expected: PASS

- [ ] **Step 3: Update DecoratorTestScenario in test_decorator_fetches_and_maps**

Line 91, change:

```python
scenario = DecoratorTestScenario(1)
```

To:

```python
scenario = DecoratorTestScenario()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_decorator_fetches_and_maps -v`

Expected: PASS

- [ ] **Step 5: Update DecoratorTestScenario in test_decorator_strict_propagates**

Lines 117-120, update:

```python
class DecoratorTestScenario(Scenario):
    @Scenario._load_step(mock_handler, Path("test"), "data.json", strict=True)
    def load_data(self, records):
        pass
```

To (no __init__ needed, just use default):

```python
class DecoratorTestScenario(Scenario):
    @Scenario._load_step(mock_handler, Path("test"), "data.json", strict=True)
    def load_data(self, records):
        pass
```

And line 122 from:

```python
scenario = DecoratorTestScenario(1)
```

To:

```python
scenario = DecoratorTestScenario()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_decorator_strict_propagates -v`

Expected: PASS

- [ ] **Step 7: Update DecoratorTestScenario in test_decorator_non_strict_continues**

Lines 137-142, update:

```python
class DecoratorTestScenario(Scenario):
    error_caught = False

    @Scenario._load_step(mock_handler, Path("test"), "data.json", strict=False)
    def load_data(self, records):
        pass
```

To (no __init__ needed):

```python
class DecoratorTestScenario(Scenario):
    error_caught = False

    @Scenario._load_step(mock_handler, Path("test"), "data.json", strict=False)
    def load_data(self, records):
        pass
```

And line 144 from:

```python
scenario = DecoratorTestScenario(1)
```

To:

```python
scenario = DecoratorTestScenario()
```

- [ ] **Step 8: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_decorator_non_strict_continues -v`

Expected: PASS

- [ ] **Step 9: Update DecoratorTestScenario in test_decorator_kwargs_passthrough**

Line 174, change:

```python
scenario = DecoratorTestScenario(1)
```

To:

```python
scenario = DecoratorTestScenario()
```

- [ ] **Step 10: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_decorator_kwargs_passthrough -v`

Expected: PASS

- [ ] **Step 11: Commit**

```bash
git add tests/test_scenario.py
git commit -m "test: update DecoratorTestScenario instantiations for new signature"
```

---

## Task 5: Update Remaining Direct Scenario() Instantiations

**Files:**
- Modify: `tests/test_scenario.py`

- [ ] **Step 1: Update test_scenario_get**

Line 195, change:

```python
scenario = Scenario(1)
```

To:

```python
scenario = Scenario()
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_scenario_get -v`

Expected: PASS

- [ ] **Step 3: Update test_scenario_set**

Line 206, change:

```python
scenario = Scenario(1)
```

To:

```python
scenario = Scenario()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_scenario_set -v`

Expected: PASS

- [ ] **Step 5: Update test_scenario_set_algorithm**

Line 215, change:

```python
scenario = Scenario(1)
```

To:

```python
scenario = Scenario()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_scenario_set_algorithm -v`

Expected: PASS

- [ ] **Step 7: Update test_scenario_exec_algorithm**

Line 224, change:

```python
scenario = Scenario(1)
```

To:

```python
scenario = Scenario()
```

- [ ] **Step 8: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_scenario_exec_algorithm -v`

Expected: PASS

- [ ] **Step 9: Update test_scenario_exec_algorithm_not_set**

Line 233, change:

```python
scenario = Scenario(1)
```

To:

```python
scenario = Scenario()
```

- [ ] **Step 10: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_scenario_exec_algorithm_not_set -v`

Expected: PASS

- [ ] **Step 11: Update LoadTestScenario**

Lines 251-263 and 264, update:

```python
class LoadTestScenario(Scenario):
    @Scenario._load_step(handler1, Path("test"), "step1.json")
    def load_step1(self, records):
        run_order.append("step1")

    @Scenario._load_step(handler2, Path("test"), "step2.json")
    def load_step2(self, records):
        run_order.append("step2")

    def load(self):
        self.load_step1()
        self.load_step2()


scenario = LoadTestScenario(1)
```

To:

```python
class LoadTestScenario(Scenario):
    @Scenario._load_step(handler1, Path("test"), "step1.json")
    def load_step1(self, records):
        run_order.append("step1")

    @Scenario._load_step(handler2, Path("test"), "step2.json")
    def load_step2(self, records):
        run_order.append("step2")

    def load(self):
        self.load_step1()
        self.load_step2()


scenario = LoadTestScenario()
```

- [ ] **Step 12: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_scenario_load -v`

Expected: PASS

- [ ] **Step 13: Update test_scenario_validate and test_scenario_validate_default_param**

Lines 273 and 281, change:

```python
scenario = Scenario(1)
```

To:

```python
scenario = Scenario()
```

- [ ] **Step 14: Run tests to verify they pass**

Run: `pytest tests/test_scenario.py::test_scenario_validate tests/test_scenario.py::test_scenario_validate_default_param -v`

Expected: PASS

- [ ] **Step 15: Commit**

```bash
git add tests/test_scenario.py
git commit -m "test: update remaining Scenario() instantiations"
```

---

## Task 6: Update Integration Test

**Files:**
- Modify: `tests/test_scenario.py`

- [ ] **Step 1: Update TestScenario in test_scenario_integration**

Lines 311-320 and 322, update:

```python
class TestScenario(Scenario):
    @Scenario._load_step(JsonHandler(), Path("."), "test_sales.json", strict=True)
    def load_sales(self, records):
        for r in records:
            self.set(
                TestSalesVolume, (Product, Region), (r["product_id"], r["region_id"]), r["volume"]
            )
            self.set(TestPrice, (Product, Region), (r["product_id"], r["region_id"]), r["price"])

    def load(self):
        self.load_sales()


scenario = TestScenario("test-001")
```

To:

```python
class TestScenario(Scenario):
    @Scenario._load_step(JsonHandler(), Path("."), "test_sales.json", strict=True)
    def load_sales(self, records):
        for r in records:
            self.set(
                TestSalesVolume, (Product, Region), (r["product_id"], r["region_id"]), r["volume"]
            )
            self.set(TestPrice, (Product, Region), (r["product_id"], r["region_id"]), r["price"])

    def load(self):
        self.load_sales()


scenario = TestScenario()
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_scenario_integration -v`

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_scenario.py
git commit -m "test: update integration test scenario instantiation"
```

---

## Task 7: Update TestScenario in test_scenario_pydantic_integration

**Files:**
- Modify: `tests/test_scenario.py`

- [ ] **Step 1: Update TestScenario __init__**

Lines 403-406 show the old pattern where the subclass manually handles the request. Update:

```python
class TestScenario(Scenario):
    def __init__(self, request: BaseRequest):
        super().__init__(request.request_id)
        self._request = request  # type: DemoRequest

    def response(self, multiplier: int = 1) -> BaseResponse:
```

To (simpler, base class handles it):

```python
class TestScenario(Scenario):
    def __init__(self, request: BaseRequest):
        super().__init__(request)

    def response(self, multiplier: int = 1) -> BaseResponse:
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_scenario_pydantic_integration -v`

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_scenario.py
git commit -m "test: simplify TestScenario __init__ in pydantic integration test"
```

---

## Task 8: Delete test_scenario_backward_compatibility

**Files:**
- Modify: `tests/test_scenario.py`

- [ ] **Step 1: Remove the obsolete test**

Delete lines 436-455 (`test_scenario_backward_compatibility`). This test explicitly verifies the old pattern where scenarios work without Pydantic and `_request` is None. With the new design, `_request` is always set, so this test is obsolete.

- [ ] **Step 2: Run all tests to verify they pass**

Run: `pytest tests/test_scenario.py -v`

Expected: PASS (all tests pass, backward compatibility test is gone)

- [ ] **Step 3: Commit**

```bash
git add tests/test_scenario.py
git commit -m "test: remove obsolete backward compatibility test"
```

---

## Task 9: Update test_scenario_request_attribute

**Files:**
- Modify: `tests/test_scenario.py`

- [ ] **Step 1: Update test assertion**

Lines 369-373 test that `_request` is initialized to None. Update:

```python
def test_scenario_request_attribute():
    """Test Scenario has _request attribute initialized to None."""
    scenario = Scenario(1)
    assert hasattr(scenario, "_request")
    assert scenario._request is None
```

To:

```python
def test_scenario_request_attribute():
    """Test Scenario has _request attribute initialized to BaseRequest."""
    scenario = Scenario()
    assert hasattr(scenario, "_request")
    assert isinstance(scenario._request, BaseRequest)
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_scenario_request_attribute -v`

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_scenario.py
git commit -m "test: update test_scenario_request_attribute assertion"
```

---

## Task 10: Update test_scenario_response_not_implemented and test_scenario_response_accepts_any_arguments

**Files:**
- Modify: `tests/test_scenario.py`

- [ ] **Step 1: Update test_scenario_response_not_implemented**

Line 378, change:

```python
scenario = Scenario(1)
```

To:

```python
scenario = Scenario()
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_scenario_response_not_implemented -v`

Expected: PASS

- [ ] **Step 3: Update test_scenario_response_accepts_any_arguments**

Line 385, change:

```python
scenario = Scenario(1)
```

To:

```python
scenario = Scenario()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scenario.py::test_scenario_response_accepts_any_arguments -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_scenario.py
git commit -m "test: update response tests for new signature"
```

---

## Task 11: Run Full Test Suite

**Files:**
- Test: `tests/test_scenario.py`

- [ ] **Step 1: Run complete test suite**

Run: `pytest tests/test_scenario.py -v`

Expected: All tests PASS

- [ ] **Step 2: Verify test count**

Run: `pytest tests/test_scenario.py --collect-only | grep "test_" | wc -l`

Expected: Should have removed 1 test (backward_compatibility) and added 2 tests (with_default_request, with_explicit_request). Original count was 23 tests. New count should be 24 tests.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "test: full test suite passes with BaseRequest in Scenario.__init__"
```

---

## Task 12: Update README Documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update basic usage example**

Lines 24-51 show the basic usage pattern. Update to reflect the new signature:

```python
class MyScenario(Scenario):
    def __init__(self):
        super().__init__()
        # ... rest of init


scenario = MyScenario()
```

Specifically, line 34-35:

```python
def __init__(self, version_id):
    super().__init__(version_id)
```

Becomes:

```python
def __init__(self):
    super().__init__()
```

And line 48:

```python
scenario = MyScenario("run-001")
```

Becomes:

```python
scenario = MyScenario()
```

- [ ] **Step 2: Update pydantic integration example**

Lines 76-80 show the DomainScenario. The current code:

```python
class DomainScenario(Scenario):
    def __init__(self, request: BaseRequest):
        self._request = request  # type: DomainRequest
        super().__init__(request.request_id)
        self._load_steps = self._build_load_steps()
```

Becomes (simpler):

```python
class DomainScenario(Scenario):
    def __init__(self, request: BaseRequest):
        super().__init__(request)
        self._load_steps = self._build_load_steps()
```

- [ ] **Step 3: Verify README examples are consistent**

Run: `python -c "exec(open('README.md').read().split('```')[1])"` (or manually verify the Python blocks are syntactically valid)

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: update README examples for BaseRequest in __init__"
```

---

## Task 13: Final Verification

**Files:**
- All

- [ ] **Step 1: Run full test suite one final time**

Run: `pytest tests/test_scenario.py -v --tb=short`

Expected: All 24 tests PASS

- [ ] **Step 2: Check git status**

Run: `git status`

Expected: No uncommitted changes

- [ ] **Step 3: Review git log**

Run: `git log --oneline -5`

Expected: Should see all the incremental commits from this plan

- [ ] **Step 4: Final commit if needed**

```bash
git add -A
git commit -m "feat: BaseRequest integration complete - Scenario.__init__ accepts optional request parameter"
```

---

## Self-Review Complete

**Spec coverage:**
- ✅ `Scenario.__init__` signature updated to accept `request: Optional[BaseRequest] = None`
- ✅ Default `BaseRequest()` created when None
- ✅ `_request` always set to valid instance (type changed from `Optional[BaseRequest]` to `BaseRequest`)
- ✅ All tests updated to use new signature
- ✅ README examples updated
- ✅ Backward compatibility test removed (old pattern no longer supported)

**Placeholder scan:**
- ✅ No "TBD", "TODO", or "implement later" found
- ✅ All code blocks contain complete implementations
- ✅ All test updates show exact line changes

**Type consistency:**
- ✅ `_request` type is `BaseRequest` throughout
- ✅ Method signature matches spec
- ✅ All instantiations updated consistently

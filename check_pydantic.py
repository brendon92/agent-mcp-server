from pydantic import BaseModel
try:
    print(f"Pydantic version check")
    class Test(BaseModel):
        foo: str = "bar"
    t = Test()
    try:
        print(f"model_dump: {t.model_dump()}")
    except AttributeError:
        print("model_dump not found, using dict()")
except Exception as e:
    print(f"Error: {e}")

use pyo3::exceptions::PySystemExit;
use pyo3::prelude::*;

fn main() -> PyResult<()> {
    Python::with_gil(|py| {
        let sys = py.import("sys")?;
        sys.setattr("argv", std::env::args().collect::<Vec<_>>())?;

        let cli = py.import("adqa.cli")?;
        match cli.call_method0("main") {
            Ok(_) => Ok(()),
            Err(err) => {
                if err.is_instance_of::<PySystemExit>(py) {
                    let code_obj = err.value(py).getattr("code")?;
                    if let Ok(code) = code_obj.extract::<i32>() {
                        if code == 0 {
                            return Ok(());
                        }
                    }
                }
                Err(err)
            }
        }
    })
}
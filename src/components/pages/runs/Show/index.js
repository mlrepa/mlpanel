import React from "react";
import {
  Show,
  SimpleShowLayout,
  TopToolbar,
  ListButton,
  TextField as FieldWithText,
  ArrayField,
  NumberField,
  Datagrid,
  UrlField,
  DeleteButton
} from "react-admin";
import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogTitle from "@material-ui/core/DialogTitle";
import DialogContentText from "@material-ui/core/DialogContentText";
import DialogContent from "@material-ui/core/DialogContent";
import DialogActions from "@material-ui/core/DialogActions";
import TextField from "@material-ui/core/TextField";
import Select from "@material-ui/core/Select";
import MenuItem from "@material-ui/core/MenuItem";

import { stringify } from "query-string";

import FormattedDateField from "../../../shared/FormattedDateField";

const RunTitle = ({ record }) => {
  return <span>{`Run ${record ? `"${record.info["run_id"]}"` : ""}`}</span>;
};

const RunShowActions = ({ basePath, data, resource }) => {
  const [open, setOpen] = React.useState(false);
  const [models, setModels] = React.useState([]);

  React.useEffect(() => {
    const currentEntities = JSON.parse(
      localStorage.getItem("current_entities")
    );
    fetch(
      `http://35.227.124.46:8080/registered-models?${stringify(
        currentEntities
      )}`,
      {
        method: "GET"
      }
    )
      .then(r => r.json())
      .then(res => {
        setModels(res);
      })
      .catch(err => console.log(err));
  }, []);

  const [modelName, setModelName] = React.useState("");
  const [selectValue, setSelectValue] = React.useState("create");

  const handleClose = () => setOpen(false);
  const handleOpen = () => setOpen(true);
  const handleSelectValueChange = e => setSelectValue(e.target.value);

  const handleSubmit = () => {
    const currentEntities = JSON.parse(
      localStorage.getItem("current_entities")
    );
    const body = {
      run_id: data.id,
      source: modelName || selectValue,
      name: modelName || selectValue
    };
    const searchParams = Object.keys(body)
      .map(key => {
        return encodeURIComponent(key) + "=" + encodeURIComponent(body[key]);
      })
      .join("&");
    fetch(
      `http://35.227.124.46:8080/registered-models?${stringify(
        currentEntities
      )}`,
      {
        method: "POST",
        body: searchParams,
        headers: new Headers({
          "Content-Type": `application/x-www-form-urlencoded`
        })
      }
    )
      .then(r => r.json())
      .then(() => {
        handleClose();
        setModelName("");
        setSelectValue("create");
      })
      .catch(err => console.log(err));
  };

  return (
    <TopToolbar>
      <Button
        className="button"
        variant="outlined"
        onClick={() => handleOpen()}
      >
        Register Modal
      </Button>
      <ListButton basePath={basePath} />
      <DeleteButton basePath={basePath} record={data} resource={resource} />
      <Dialog
        open={open}
        onClose={handleClose}
        aria-labelledby="form-dialog-title"
      >
        <DialogTitle id="form-dialog-title">Register Model</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Once registered, the model will be available in the model registry
            and become public.
          </DialogContentText>
          <Select
            style={{ width: 200, marginBottom: 20 }}
            value={selectValue}
            defaultValue={"create"}
            onChange={handleSelectValueChange}
          >
            <MenuItem value={"create"}>Create New Model</MenuItem>
            {models &&
              models.map(item => (
                <MenuItem key={item.id} value={item.id}>
                  {item.id}
                </MenuItem>
              ))}
          </Select>
          <TextField
            required
            autoFocus
            label="Model name"
            type="text"
            fullWidth
            disabled={selectValue !== "create"}
            value={modelName}
            onChange={e => setModelName(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} variant="outlined">
            Cancel
          </Button>
          <Button
            onClick={() => {
              if (modelName || selectValue !== "create") {
                handleSubmit();
              }
            }}
            variant="contained"
            color="primary"
          >
            Register
          </Button>
        </DialogActions>
      </Dialog>
    </TopToolbar>
  );
};

const RunShow = props => {
  return (
    <Show actions={<RunShowActions />} title={<RunTitle />} {...props}>
      <SimpleShowLayout>
        <FieldWithText label="Run" source="id" />
        <UrlField label="Artifact URI" source="info.artifact_uri" />
        <FieldWithText label="Status" source="info.status" />
        <FieldWithText label="Lifecycle stage" source="info.lifecycle_stage" />
        <FormattedDateField innerProp="info" source="start_time" />
        <FormattedDateField innerProp="info" source="end_time" />
        <ArrayField label="Metrics" source="data.metrics">
          <Datagrid>
            <FieldWithText source="key" />
            <NumberField source="value" />
            <FormattedDateField source="timestamp" />
            <FieldWithText source="step" />
          </Datagrid>
        </ArrayField>
        <ArrayField label="Params" source="data.params">
          <Datagrid>
            <FieldWithText source="key" />
            <NumberField source="value" />
          </Datagrid>
        </ArrayField>
        <ArrayField label="Tags" source="data.tags">
          <Datagrid>
            <FieldWithText source="key" />
            <NumberField source="value" />
          </Datagrid>
        </ArrayField>
      </SimpleShowLayout>
    </Show>
  );
};

export default RunShow;

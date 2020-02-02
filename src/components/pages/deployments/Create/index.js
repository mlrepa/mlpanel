import React from "react";
import { SimpleShowLayout, Create, TopToolbar, ListButton } from "react-admin";
import { stringify } from "query-string";
import Button from "@material-ui/core/Button";
import Select from "@material-ui/core/Select";
import MenuItem from "@material-ui/core/MenuItem";

const DeploymentCreateActions = ({ basePath }) => (
  <TopToolbar>
    <ListButton basePath={basePath} />
  </TopToolbar>
);

const DeploymentCreate = props => {
  const [models, setModels] = React.useState([]);
  const [selectValue, setSelectValue] = React.useState("");
  const [modelVersions, setModelVersions] = React.useState([]);

  React.useEffect(() => {
    const currentEntities = JSON.parse(
      localStorage.getItem("current_entities")
    );
    if (selectValue) {
      fetch(
        `http://35.227.124.46:8080/model-versions?${stringify(
          currentEntities
        )}&model_id=${selectValue.id}`,
        {
          method: "GET"
        }
      )
        .then(r => r.json())
        .then(res => {
          setModelVersions(res);
        })
        .catch(err => console.log(err));
    }
  }, [selectValue]);

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

  const handleDeploy = () => {
    const currentEntities = JSON.parse(
      localStorage.getItem("current_entities")
    );
    fetch(
      `http://35.227.124.46:8080/deployments?${stringify(
        currentEntities
      )}&version=${modelVersions[modelVersions.length - 1].version}&model_id=${
        selectValue.id
      }&type=local`,
      {
        method: "POST"
      }
    )
      .then(r => r.json())
      .then(res => {
        alert(res.message);
      })
      .catch(err => alert(err));
  };
  return (
    <Create actions={<DeploymentCreateActions />} {...props}>
      <SimpleShowLayout saving={false}>
        <Select
          style={{ width: 200 }}
          value={selectValue}
          onChange={e => setSelectValue(e.target.value)}
        >
          {models &&
            models.map(item => (
              <MenuItem key={item.id} value={item}>
                {item.id}
              </MenuItem>
            ))}
        </Select>
        {selectValue && (
          <Button
            style={{ width: 200, marginTop: 20 }}
            variant="contained"
            color="primary"
            onClick={() => handleDeploy()}
          >
            Deploy
          </Button>
        )}
      </SimpleShowLayout>
    </Create>
  );
};

export default DeploymentCreate;

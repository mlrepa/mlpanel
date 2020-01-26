import React from "react";
import { connect } from "react-redux";
import { List, Datagrid, TextField, ShowButton } from "react-admin";

import FormattedDateField from "../../../shared/FormattedDateField";

const ExperimentList = props => {
  const { activeProjectId, dispatch, ...restProps } = props;

  return (
    <List {...restProps} filter={{ project_id: activeProjectId }}>
      <Datagrid>
        <TextField source="name" />
        <TextField source="lifecycle_stage" />
        <FormattedDateField source="last_update_time" />
        <FormattedDateField source="creation_time" />
        <ShowButton />
      </Datagrid>
    </List>
  );
};

export default connect(state => ({
  activeProjectId: state.activeProject
}))(ExperimentList);

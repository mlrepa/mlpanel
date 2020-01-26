import React from "react";
import { AppBar } from "react-admin";
import Typography from "@material-ui/core/Typography";
import EntitySelect from "../EnititySelect";
import { withStyles } from "@material-ui/core/styles";

const styles = {
  title: {
    flex: 1,
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    overflow: "hidden"
  },
  spacer: {
    flex: 1
  }
};

const CustomFlowBar = withStyles(styles)(({ classes, ...props }) => {
  const entitiesSelects = ["project", "experiment"];

  return (
    <AppBar {...props}>
      <Typography
        h1="title"
        color="inherit"
        className={classes.title}
        id="react-admin-title"
      />
      {entitiesSelects.map(item => (
        <React.Fragment key={item}>
          <EntitySelect entity={item} />
          <span className={classes.spacer} />
        </React.Fragment>
      ))}
    </AppBar>
  );
});

export default CustomFlowBar;

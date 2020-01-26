import React from "react";
import { AppBar } from "react-admin";
import Typography from "@material-ui/core/Typography";
import ActiveProjectContextSwitcher from "../ProjectSelect";
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

const CustomFlowBar = withStyles(styles)(({ classes, ...props }) => (
  <AppBar {...props}>
    <Typography
      h1="title"
      color="inherit"
      className={classes.title}
      id="react-admin-title"
    />
    <ActiveProjectContextSwitcher />
    <span className={classes.spacer} />
  </AppBar>
));

export default CustomFlowBar;

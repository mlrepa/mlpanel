import React from 'react';
import { AppBar } from 'react-admin';
import Typography from '@material-ui/core/Typography';
import ActiveProjectContextSwitcher from '../activeProjectContext/ActiveProjectContextSwitcher';
import { withStyles } from '@material-ui/core/styles';

// import Logo from './Logo';

const styles = {
    title: {
        flex: 1,
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        overflow: 'hidden',
    },
    spacer: {
        flex: 1,
    },
};

const CustomflowBar = withStyles(styles)(({ classes, ...props }) => (
    <AppBar {...props}>
        <Typography
            h1="title"
            color="inherit"
            className={classes.title}
            id="react-admin-title"
        />
        {/* <Logo /> */}
        <ActiveProjectContextSwitcher />
        <span className={classes.spacer} />
    </AppBar>
));

export default CustomflowBar;
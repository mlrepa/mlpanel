
POSITIONAL_ARGS=()

while [ "$1" != "" ]; do
    case "$1" in
        --edition)
            shift
            EDITION=$1
            ;;
        *)
        POSITIONAL_ARGS+=("$1")
    esac
    shift
done;


check_input_edition(){
  if [ -z $EDITION ]; then
    echo "WARNING: edition not specified, base edition selected by default."
    EDITION='base'
  fi;
}


help(){

  SCRIPT=$1
  EDITION_INFO="[--edition <name>].\nDefault edition: base."
  case $SCRIPT in
  "build")
    printf "Builds images.\nSyntax: ./build.sh $EDITION_INFO\nExamples:
    \t./build.sh\n\t./build.sh --edition base\n"
    ;;

  "start")
    printf "Starts mlpanel.\nSyntax: ./start.sh $EDITION_INFO\nExamples:
    \t./build.sh\n\t./start.sh --edition base\n"
    ;;

  "restart")
    printf "Restarts several or all services. If services not specified then restarts all
    \nSyntax: ./retart.sh [<service_name1>, <service_name2>, ...] $EDITION_INFO\nExamples:
    \t./restart.sh\n\t./restart.sh web\n\t./restart.sh web --edition base\n"
    ;;

  "stop")

    printf "Stops mlpanel.\nSyntax: ./stop.sh $EDITION_INFO\nExamples:
    \t./build.sh\n\t./build.sh --edition base\n"
    ;;
  esac

  exit
}

handle_help(){
  if [ '--help' == "${POSITIONAL_ARGS[0]}" ]; then
    help $1
  fi;
}
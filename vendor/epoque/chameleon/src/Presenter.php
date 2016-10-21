<?php
namespace Epoque\Chameleon;


/**
 * Description of Presenter
 *
 * @author jason
 */

class Presenter extends Common implements RouterInterface
{
    private static $routes = [];
    
    
    public static function addRoute($route=array()) {
        if ( is_array($route) && !empty($route) && is_string(key($route)) &&
                ( is_file(current($route)) || is_file(VIEWS_DIR.current($route)) ) )
        {
            self::$routes[trim(key($route), '/')] = current($route);
            return true;
        }
        else {
            self::logWarning(__METHOD___ . ': could not add route [' . key($route) .
                    ' => ' . current($route) . 'failed.');
            return false;
        }
    }

    
    public static function fetchRoute() {
        if (array_key_exists(self::URI(), self::$routes)) {
            if (is_file(self::$routes[self::URI()])) {
                include_once self::$routes[self::URI()];
            }
            else if (is_file(VIEWS_DIR . self::$routes[self::URI()])) {
                include VIEWS_DIR . self::$routes[self::URI()];
            }
            else if (is_file(VIEWS_DIR . self::URI() . '.php')) {
                include VIEWS_DIR . self::URI() . '.php';
            }
            else {
                self::logWarning(__METHOD___ . ': could not fetch requested (' +
                        self::URI() + ') route.');
            }
        }
        else if (is_file(DEFAULT_VIEW)) {
            include_once DEFAULT_VIEW;
            self::logWarning(__METHOD__ . ': URI ('.self::URI().') not a route, showing default view (' . DEFAULT_VIEW . ')');
        }
        else if (is_file(ERROR_404_FILE)) {
            include_once(ERROR_404_FILE);
            self::logWarning(__METHOD__ . ': URI ('.self::URI().') not a route, default view (' . DEFAULT_VIEW . ') is not a file.');
        }
        else {
            self::logError(__METHOD__ . ': failed URI (' . self::URI() . ').');
        }
    }

}

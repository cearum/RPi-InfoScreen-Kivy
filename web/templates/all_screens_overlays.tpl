% rebase("base.tpl", title="Installed Screens")
<form action="/" method="POST">
<table class="centre">
    <input type="hidden" name="test" value="OK" />
    % for screen in screens:
    <tr>
        <td width="30%">{{screen.capitalize()}}</td>
        <td><button name="submit" type="submit" value="view+{{screen}}"
            % if not screens[screen]["enabled"]:
            disabled
            % end
            >View</button></td>
        <td><button name="submit" type="submit" value="enable+{{screen}}"
            % if screens[screen]["enabled"]:
            disabled
            % end
            >Enable</button></td>
        <td><button name="submit" type="submit" value="disable+{{screen}}"
            % if not screens[screen]["enabled"]:
            disabled
            % end
            >Disable</button></td>
        <td><button name="submit" type="submit" value="configure+{{screen}}">
            Configure</button></td>
        <td><button name="submit" type="submit" value="custom+{{screen}}"
            % if not screens[screen]["web"]:
            disabled
            % end
            >Custom</button></td>
    </tr>
    % end
</table>
</form>

<h2>Installed Overlays</h2>
<form action="/" method="POST">
<table class="centre">
    <input type="hidden" name="test" value="OK" />
    % for overlay in overlays:
    <tr>
        <td width="30%">{{overlay.capitalize()}}</td>
        <td><button name="submit" type="submit" value="view+{{overlay}}+overlay"
            % if not overlays[overlay]["enabled"]:
            disabled
            % end
            >View</button></td>
        <td><button name="submit" type="submit" value="enable+{{overlay}}+overlay"
            % if overlays[overlay]["enabled"]:
            disabled
            % end
            >Enable</button></td>
        <td><button name="submit" type="submit" value="disable+{{overlay}}+overlay"
            % if not overlays[overlay]["enabled"]:
            disabled
            % end
            >Disable</button></td>
        <td><button name="submit" type="submit" value="configure+{{overlay}}+overlay">
            Configure</button></td>
        <td><button name="submit" type="submit" value="custom+{{overlay}}+overlay"
            % if not overlays[overlay]["web"]:
            disabled
            % end
            >Custom</button></td>
    </tr>
    % end
</table>
</form>
